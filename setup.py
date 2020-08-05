# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

version = "1.2.3"

with open("README.rst", "r") as fh:
    long_description = fh.read()

with open("docs/changelog.rst", "r") as fh:
    long_description += "\n\n"
    long_description += fh.read()

setup(
    name="senaite.jsonapi",
    version=version,
    description="SENAITE JSON API",
    long_description=long_description,
    # Get more strings from
    # http://pypi.python.org/pypi?:action=list_classifiers
    classifiers=[
        "Framework :: Plone",
        "Framework :: Zope2",
        "Programming Language :: Python",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
    keywords="",
    author="RIDING BYTES & NARALABS",
    author_email="senaite@senaite.com",
    url="https://github.com/senaite/senaite.jsonapi",
    license="GPLv2",
    packages=find_packages("src", exclude=["ez_setup"]),
    package_dir={"": "src"},
    namespace_packages=["senaite"],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "setuptools",
        "senaite.core",
    ],
    extras_require={
        "test": [
            "Products.PloneTestCase",
            "Products.SecureMailHost",
            "plone.app.testing",
            "unittest2",
        ]
    },
    entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
)
