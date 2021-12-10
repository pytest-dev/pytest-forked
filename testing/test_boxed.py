import os

import pytest

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


def test_is_not_boxed_by_default(testdir):
    config = testdir.parseconfig(testdir.tmpdir)
    assert not config.option.forked
