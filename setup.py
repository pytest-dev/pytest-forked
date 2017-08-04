from setuptools import setup

setup(
    name="pytest-forked",
    use_scm_version=True,
    description='run tests in isolated forked subprocesses',
    long_description=open('README.rst').read(),
    license='MIT',
    author='pytest-dev',
    author_email='pytest-dev@python.org',
    url='https://github.com/pytest-dev/pytest-forked',
    platforms=['linux', 'osx'],
    packages=['pytest_forked'],
    package_dir={'': 'src'},
    entry_points={
        'pytest11': [
            'pytest_forked = pytest_forked',
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
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
)
