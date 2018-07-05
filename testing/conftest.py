import pytest


pytest_plugins = "pytester"


@pytest.fixture(autouse=True)
def _divert_atexit(request, monkeypatch):
    import atexit
    atexit_fns = []

    def finish():
        while atexit_fns:
            atexit_fns.pop()()

    monkeypatch.setattr(atexit, "register", atexit_fns.append)
    request.addfinalizer(finish)
