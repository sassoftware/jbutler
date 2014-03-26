# Copyright (c) 2013 SAS Institute, Inc
#
from setuptools import setup, find_packages

from jbutler.constants import VERSION

setup(
    name='jbutler',
    version=VERSION,
    description='Manage a Jenkins instance',
    author='Walter Scheper',
    author_email='walter.scheper@sas.com',
    license='Apache License 2.0',
    packages=find_packages(exclude=['jbutler_test']),
    scripts=['commands/jbutler']
    )
