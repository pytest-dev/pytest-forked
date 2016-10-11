from setuptools import setup

setup(
    name="pytest-boxed",
    use_scm_version=True,
    description='run tests in isolated subprocessesfor distributed testing'
                ' and loop-on-failing modes',
    long_description=open('README.rst').read(),
    license='MIT',
    author='holger krekel and contributors',
    author_email='pytest-dev@python.org',
    url='https://github.com/pytest-dev/pytest-xdist',
    platforms=['linux', 'osx'],
    packages=['pytest_boxed'],
    package_dir={'': 'src'},
    entry_points={
        'pytest11': [
            'pytest_boxed = pytest_boxed',
        ],
    },
    zip_safe=False,
    install_requires=['pytest>=2.6.0'],
    setup_requires=['setuptools_scm'],
    classifiers=[
        'Development Status :: 7 - Inactive',
        'Framework :: Pytest',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Utilities',
        'Programming Language :: Python',
        'Programming Language :: Python :: ',
        'Programming Language :: Python :: 3',
    ],
)
