#!/usr/bin/env python
import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.txt')) as f:
    CHANGES = f.read()

install_requires = [
    'requests>=2.6.0',
    'elasticsearch>=1.3.0',
    'cython>=0.22',
    'thriftpy>=0.2.0',
    'thriftpywrap',
    'xylose',
    'elasticsearch-dsl',
    'pyramid>=1.5.7',
    'pyramid_chameleon',
    'pyramid_mako',
    'pyramid_debugtoolbar',
    'waitress',
    ]

test_requires = []

setup(
    name="publication",
    version='0.2.8',
    description="A SciELO RPC server and API to retrieve publication statistics from the SciELO Network ",
    author="SciELO",
    author_email="scielo-dev@googlegroups.com",
    license="BSD 2-clause",
    url="http://docs.scielo.org",
    keywords='scielo statistics',
    packages=['publication'],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Operating System :: POSIX :: Linux",
        "Topic :: System",
        "Topic :: Services",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    dependency_links=[
        "git+https://github.com/scieloorg/xylose@0.33#egg=xylose",
        "git+https://github.com/scieloorg/thriftpy-wrap@0.1.1#egg=thriftpywrap",
        "-e git+https://github.com/elastic/elasticsearch-dsl-py@0.0.9#egg=elasticsearch-dsl"
    ],
    include_package_data=True,
    zip_safe=False,
    setup_requires=["nose>=1.0", "coverage"],
    tests_require=test_requires,
    install_requires=install_requires,
    test_suite="nose.collector",
    entry_points="""\
    [paste.app_factory]
    main = publication:main
    [console_scripts]
    publicationstats_thriftserver = publication.thrift.server:main
    publicationstats_loaddata = processing.loaddata:main
    """,
)