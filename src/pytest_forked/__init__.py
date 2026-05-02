import marshal
import multiprocessing
import os
import sys
import tempfile
import warnings

import pytest
from _pytest import runner

# we know this bit is bad, but we cant help it with the current pytest setup

# copied from xdist remote
def serialize_report(rep):
    d = rep.__dict__.copy()
    if hasattr(rep.longrepr, "toterminal"):
        d["longrepr"] = str(rep.longrepr)
    else:
        d["longrepr"] = rep.longrepr
    for name in d:
        if isinstance(d[name], os.PathLike):
            d[name] = os.fspath(d[name])
        elif name == "result":
            d[name] = None  # for now
    return d


def pytest_addoption(parser):
    group = parser.getgroup("forked", "forked subprocess test execution")
    group.addoption(
        "--forked",
        action="store_true",
        dest="forked",
        default=False,
        help="box each test run in a separate process (unix)",
    )


def pytest_load_initial_conftests(early_config, parser, args):
    early_config.addinivalue_line(
        "markers",
        "forked: Always fork for this test.",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_protocol(item, nextitem):
    if item.config.getvalue("forked") or item.get_closest_marker("forked"):
        ihook = item.ihook
        ihook.pytest_runtest_logstart(nodeid=item.nodeid, location=item.location)
        reports = forked_run_report(item)
        for rep in reports:
            ihook.pytest_runtest_logreport(report=rep)
        item.session._setupstate.teardown_exact(nextitem)
        ihook.pytest_runtest_logfinish(nodeid=item.nodeid, location=item.location)
        return True


class _ForkedResult:
    """Mimics py.process.ForkedFunc result object."""

    def __init__(self):
        self.retval = None
        self.exitstatus = 0
        self.signal = 0
        self.out = ""
        self.err = ""


def _worker(runforked_fn, stdout_path, stderr_path, retval_path):
    """
    Child process entry point.
    Redirects OS-level fds 1 and 2 to files before running the test,
    so output is captured even if the process is killed by a signal.
    """
    EXITSTATUS_EXCEPTION = 3

    # Redirect stdout/stderr at the OS fd level (survives hard crashes)
    stdout_fd = os.open(stdout_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
    stderr_fd = os.open(stderr_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
    os.dup2(stdout_fd, 1)
    os.dup2(stderr_fd, 2)
    os.close(stdout_fd)
    os.close(stderr_fd)

    # redirect Python-level streams so print() etc. work
    sys.stdout = open(stdout_path, "w", buffering=1)
    sys.stderr = open(stderr_path, "w", buffering=1)

    try:
        retval = runforked_fn()
        with open(retval_path, "wb") as f:
            f.write(retval)
    except KeyboardInterrupt:
        os._exit(4)  # EXITSTATUS_TESTEXIT
    except SystemExit as e:
        code = e.code if e.code is not None else 0
        os._exit(int(code))
    except Exception:
        os._exit(EXITSTATUS_EXCEPTION)
    finally:
        try:
            sys.stdout.flush()
            sys.stderr.flush()
        except Exception:
            pass

    os._exit(0)


def forked_run_report(item):
    from _pytest.runner import runtestprotocol

    EXITSTATUS_TESTEXIT = 4

    def runforked():
        try:
            reports = runtestprotocol(item, log=False)
        except KeyboardInterrupt:
            os._exit(EXITSTATUS_TESTEXIT)
        return marshal.dumps([serialize_report(x) for x in reports])

    # Use temp files for stdout/stderr — captured at OS fd level, so they
    # survive a SIGKILL/SIGTERM just like the original ForkedFunc did.
    with tempfile.TemporaryDirectory() as tmpdir:
        stdout_path = os.path.join(tmpdir, "stdout")
        stderr_path = os.path.join(tmpdir, "stderr")
        retval_path = os.path.join(tmpdir, "retval")

        # Pre-create files so reads don't fail if child never writes
        open(stdout_path, "w").close()
        open(stderr_path, "w").close()
        ctx = multiprocessing.get_context("fork")
        proc = ctx.Process(
            target=_worker,
            args=(runforked, stdout_path, stderr_path, retval_path),
        )
        proc.start()
        proc.join()

        result = _ForkedResult()
        result.exitstatus = proc.exitcode if proc.exitcode is not None else 0

        # Decode signal number from exit code the same way waitpid does:
        # multiprocessing sets exitcode = -signum for signal-killed children
        if proc.exitcode is not None and proc.exitcode < 0:
            result.signal = -proc.exitcode

        # Read captured output — available even after a crash
        try:
            with open(stdout_path) as f:
                result.out = f.read()
        except OSError:
            result.out = ""

        try:
            with open(stderr_path) as f:
                result.err = f.read()
        except OSError:
            result.err = ""

        # Read return value only if child exited cleanly (no signal, no error)
        if result.signal == 0 and result.exitstatus == 0:
            try:
                with open(retval_path, "rb") as f:
                    retval_data = f.read()
                if retval_data:
                    result.retval = retval_data
            except OSError:
                result.retval = None

    if result.retval is not None:
        report_dumps = marshal.loads(result.retval)
        return [runner.TestReport(**x) for x in report_dumps]
    else:
        if result.exitstatus == EXITSTATUS_TESTEXIT:
            pytest.exit(f"forked test item {item} raised Exit")
        return [report_process_crash(item, result)]


def report_process_crash(item, result):
    import signal as signal_module

    # getfslineno returns -1 when called from the parent process on an item
    # whose source is only resolvable in the child. Use the item's own
    # location (nodeid path + fspath) which is always populated by pytest.
    try:
        from _pytest._code import getfslineno

        path, lineno = getfslineno(item)
        if lineno == -1:
            raise ValueError("unresolvable")
    except Exception:
        path = getattr(item, "fspath", None) or item.nodeid.split("::")[0]
        lineno = item.location[1] if item.location[1] is not None else 0

    if result.signal:
        try:
            sig_name = signal_module.Signals(result.signal).name
        except ValueError:
            sig_name = "UNKNOWN"
        info = "%s:%s: running the test CRASHED with signal %d (%s)" % (
            path,
            lineno,
            result.signal,
            sig_name,
        )

        info_bare = "%s:%s: running the test CRASHED with signal %d" % (
            path,
            lineno,
            result.signal,
        )
    else:
        info = "%s:%s: running the test EXITED with status %d" % (
            path,
            lineno,
            result.exitstatus,
        )
        info_bare = info

    from _pytest import runner

    # pytest >= 4.1
    has_from_call = getattr(runner.CallInfo, "from_call", None) is not None
    if has_from_call:
        call = runner.CallInfo.from_call(lambda: 0 / 0, "???")
    else:
        call = runner.CallInfo(lambda: 0 / 0, "???")
    call.excinfo = info
    rep = runner.pytest_runtest_makereport(item, call)
    if result.out:
        rep.sections.append(("captured stdout", result.out))
    if result.err:
        rep.sections.append(("captured stderr", result.err))

    xfail_marker = item.get_closest_marker("xfail")
    if not xfail_marker:
        return rep

    rep.outcome = "skipped"

    xfail_reason = xfail_marker.kwargs.get(
        "reason",
        xfail_marker.args[0] if xfail_marker.args else "",
    )
    rep.wasxfail = (
        "reason: {xfail_reason}; "
        "pytest-forked reason: {crash_info}".format(
            xfail_reason=xfail_reason,
            crash_info=info_bare,
        )
    )
    warnings.warn(
        "pytest-forked xfail support is incomplete at the moment and may "
        "output a misleading reason message",
        RuntimeWarning,
    )

    return rep
