pytest-boxed: run each test in a boxed subprocess
=================================================



* ``--boxed``: (not available on Windows) run each test in a boxed_
  subprocess to survive ``SEGFAULTS`` or otherwise dying processes

this plugins is currently deprecated and no longer maintained,
it was purely extracted to keep backward compat without burdening xdist


Installation
-----------------------

Install the plugin with::

    pip install pytest-boxed

or use the package in develope/in-place mode with
a checkout of the `pytest-xdist repository`_ ::

   pip install -e .

Usage examples
---------------------

If you have tests involving C or C++ libraries you might have to deal
with tests crashing the process.  For this case you may use the boxing
options::

    py.test --boxed

which will run each test in a subprocess and will report if a test
crashed the process.  You can also combine this option with
running multiple processes via pytest-xdist to speed up the test run
and use your CPU cores::

    py.test -n3 --boxed

this would run 3 testing subprocesses in parallel which each
create new boxed subprocesses for each test.
