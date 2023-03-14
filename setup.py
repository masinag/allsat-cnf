import os
from os import path

from setuptools import find_packages, setup

NAME = 'local-tseitin'
DESCRIPTION = ''
URL = 'http://gitlab.com/giuspek/local-tseitin'
EMAIL = ''
AUTHOR = ''
REQUIRES_PYTHON = '>=3.5.0'
VERSION = '0.1'

# What packages are required for this module to be executed?
REQUIRED = [
    'pysmt',
    'py-aiger >= 6.2.0',
    'circuitgraph >= 0.2.0',
    'funcy >= 1.17',
    'psutil>=5.9.4',
]

# What packages are optional?
EXTRAS = {
    'test': ['pytest', 'pytest-cov', 'pytest-benchmark'],
    'benchmark': [
        'matplotlib',
        'pandas',
        'tqdm',
        'wmipa',
        'wmibench @ git+ssh://git@github.com/paolomorettin/hybrid-benchmarks.git@Gauss#egg=wmibench',
    ],
}

here = os.path.abspath(os.path.dirname(__file__))

with open(path.join(here, 'README.md')) as ref:
    long_description = ref.read()

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    url=URL,
    author=AUTHOR,
    author_email=EMAIL,
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
    python_requires=REQUIRES_PYTHON,
    packages=find_packages(exclude=('test', 'examples')),
    zip_safe=False,
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    cmdclass={
        #        'upload': UploadCommand,
        #        'install': PostInstallCommand,
    },
)
