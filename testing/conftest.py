import pytest


pytest_plugins = "pytester"


@pytest.fixture(autouse=True)
def _divert_atexit(request, monkeypatch):
    import atexit
    atexit_fns = []

    def atexit_register(func, *args, **kwargs):
        atexit_fns.append(lambda: func(*args, **kwargs))

    def finish():
        while atexit_fns:
            atexit_fns.pop()()

    monkeypatch.setattr(atexit, "register", atexit_register)
    request.addfinalizer(finish)
