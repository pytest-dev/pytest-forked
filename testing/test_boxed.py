import marshal
import os

import pytest
from _pytest.reports import TestReport

from pytest_forked import serialize_report

needsfork = pytest.mark.skipif(not hasattr(os, "fork"), reason="os.fork required")


@needsfork
def test_functional_boxed(testdir):
    p1 = testdir.makepyfile(
        """
        import os
        def test_function():
            os.kill(os.getpid(), 15)
    """
    )
    result = testdir.runpytest(p1, "--forked")
    result.stdout.fnmatch_lines(["*CRASHED*", "*1 failed*"])


@needsfork
def test_functional_boxed_per_test(testdir):
    p1 = testdir.makepyfile(
        """
        import os
        import pytest

        @pytest.mark.forked
        def test_function():
            os.kill(os.getpid(), 15)
    """
    )
    result = testdir.runpytest(p1)
    result.stdout.fnmatch_lines(["*CRASHED*", "*1 failed*"])


@needsfork
@pytest.mark.parametrize(
    "capmode",
    [
        "no",
        pytest.param("sys", marks=pytest.mark.xfail(reason="capture cleanup needed")),
        pytest.param("fd", marks=pytest.mark.xfail(reason="capture cleanup needed")),
    ],
)
def test_functional_boxed_capturing(testdir, capmode):
    p1 = testdir.makepyfile(
        """
        import os
        import sys
        def test_function():
            sys.stdout.write("hello\\n")
            sys.stderr.write("world\\n")
            os.kill(os.getpid(), 15)
    """
    )
    result = testdir.runpytest(p1, "--forked", "--capture=%s" % capmode)
    result.stdout.fnmatch_lines(
        """
        *CRASHED*
        *stdout*
        hello
        *stderr*
        world
        *1 failed*
"""
    )


@needsfork
def test_crash_message_shows_signal_name(testdir):
    p1 = testdir.makepyfile(
        """
        import os, signal
        def test_function():
            os.kill(os.getpid(), signal.SIGTERM)
    """
    )
    result = testdir.runpytest(p1, "--forked")
    result.stdout.fnmatch_lines(["*CRASHED with signal 15 (SIGTERM)*", "*1 failed*"])


@needsfork
def test_crash_message_shows_exit_status(testdir):
    p1 = testdir.makepyfile(
        """
        import os
        def test_function():
            os._exit(42)
    """
    )
    result = testdir.runpytest(p1, "--forked")
    result.stdout.fnmatch_lines(["*EXITED with status 42*", "*1 failed*"])


@needsfork
def test_forked_followed_by_other_test_tears_down(testdir):
    testdir.makepyfile(
        test_a="""
        import pytest

        def test_unforked():
            assert True

        @pytest.mark.forked
        def test_forked():
            assert True
        """,
        test_b="""
        def test_other_module():
            assert True
        """,
    )
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(["*3 passed*"])
    assert result.ret == 0


def test_is_not_boxed_by_default(testdir):
    config = testdir.parseconfig(testdir.tmpdir)
    assert not config.option.forked


def test_serialize_report_roundtrips_through_marshal():
    rep = TestReport(
        "test_x.py::test_y",
        ("test_x.py", 1, "test_y"),
        {},
        "passed",
        None,
        "call",
        [],
        0.1,
        0.0,
        0.1,
        [],
    )
    d = marshal.loads(marshal.dumps(serialize_report(rep)))
    assert "_id" not in d
    rebuilt = TestReport(**d)
    assert rebuilt.nodeid == rep.nodeid
    assert rebuilt.outcome == "passed"


@needsfork
def test_child_exception_traceback_is_reported(testdir):
    p1 = testdir.makepyfile(
        """
        def test_function(record_property):
            record_property("obj", object())
        """
    )
    result = testdir.runpytest(p1, "--forked")
    result.stdout.fnmatch_lines(
        [
            "*EXITED with status 3*",
            "*ValueError: unmarshallable object*",
            "*1 failed*",
        ]
    )
