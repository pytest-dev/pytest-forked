"""Tests for xfail support."""
import os
import signal

import pytest

IS_PYTEST4_PLUS = int(pytest.__version__[0]) >= 4  # noqa: WPS609
FAILED_WORD = "FAILED" if IS_PYTEST4_PLUS else "FAIL"

pytestmark = pytest.mark.skipif(  # pylint: disable=invalid-name
    not hasattr(os, "fork"),  # noqa: WPS421
    reason="os.fork required",
)


@pytest.mark.parametrize(
    ("is_crashing", "is_strict"),
    (
        pytest.param(True, True, id="strict xfail"),
        pytest.param(False, True, id="strict xpass"),
        pytest.param(True, False, id="non-strict xfail"),
        pytest.param(False, False, id="non-strict xpass"),
    ),
)
def test_xfail(is_crashing, is_strict, testdir):
    """Test xfail/xpass/strict permutations."""
    # pylint: disable=possibly-unused-variable
    sig_num = signal.SIGTERM.numerator

    test_func_body = (
        "os.kill(os.getpid(), signal.SIGTERM)" if is_crashing else "assert True"
    )

    if is_crashing:
        # marked xfailed and crashing, no matter strict or not
        expected_letter = "x"  # XFAILED
        expected_lowercase = "xfailed"
        expected_word = "XFAIL"
    elif is_strict:
        # strict and not failing as expected should cause failure
        expected_letter = "F"  # FAILED
        expected_lowercase = "failed"
        expected_word = FAILED_WORD
    elif not is_strict:
        # non-strict and not failing as expected should cause xpass
        expected_letter = "X"  # XPASS
        expected_lowercase = "xpassed"
        expected_word = "XPASS"

    session_start_title = "*==== test session starts ====*"
    loaded_pytest_plugins = "plugins: forked*"
    collected_tests_num = "collected 1 item"
    expected_progress = f"test_xfail.py {expected_letter!s}*"
    failures_title = "*==== FAILURES ====*"
    failures_test_name = "*____ test_function ____*"
    failures_test_reason = "[XPASS(strict)] The process gets terminated"
    short_test_summary_title = "*==== short test summary info ====*"
    short_test_summary = f"{expected_word!s} test_xfail.py::test_function"
    if expected_lowercase == "xpassed":
        # XPASS wouldn't have the crash message from
        # pytest-forked because the crash doesn't happen
        short_test_summary = " ".join(
            (
                short_test_summary,
                "The process gets terminated",
            )
        )
    reason_string = (
        f"  reason: The process gets terminated; "
        f"pytest-forked reason: "
        f"*:*: running the test CRASHED with signal {sig_num:d}"
    )
    total_summary_line = f"*==== 1 {expected_lowercase!s} in 0.*s* ====*"

    expected_lines = (
        session_start_title,
        loaded_pytest_plugins,
        collected_tests_num,
        expected_progress,
    )
    if expected_word == FAILED_WORD:
        # XPASS(strict)
        expected_lines += (
            failures_title,
            failures_test_name,
            failures_test_reason,
        )
    expected_lines += (
        short_test_summary_title,
        short_test_summary,
    )
    if expected_lowercase == "xpassed" and expected_word == FAILED_WORD:
        # XPASS(strict)
        expected_lines += (reason_string,)
    expected_lines += (total_summary_line,)

    test_module = testdir.makepyfile(
        f"""
        import os
        import signal

        import pytest

        # The current implementation emits RuntimeWarning.
        pytestmark = pytest.mark.filterwarnings('ignore:pytest-forked xfail')

        @pytest.mark.xfail(
            reason='The process gets terminated',
            strict={is_strict!s},
        )
        @pytest.mark.forked
        def test_function():
            {test_func_body!s}
        """
    )

    pytest_run_result = testdir.runpytest(test_module, "-ra")
    pytest_run_result.stdout.fnmatch_lines(expected_lines)
