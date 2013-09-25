# Copyright (c) 2013 SAS Institute, Inc
#
from distutils.core import setup


VERSION = (0, 0, 1)

setup(
    name='jbutler',
    version='{0}.{1}.{2}'.format(*VERSION),
    description='Manage a Jenkins instance',
    author='Walter Scheper',
    author_email='walter.scheper@sas.com',
    license='Apache License 2.0',
    packages=[
        'jbutler',
        'jbutler.commands',
        'jbutler.lib',
        'jbutler.utils',
        ],
    scripts=['commands/jbutler']
    )
