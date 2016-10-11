import pytest


pytest_plugins = "pytester"


@pytest.fixture(autouse=True)
def _divert_atexit(request, monkeypatch):
    import atexit
    l = []

    def finish():
        while l:
            l.pop()()

    monkeypatch.setattr(atexit, "register", l.append)
    request.addfinalizer(finish)
