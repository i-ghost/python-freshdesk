﻿from setuptools import find_packages, setup

setup(
    name='python-freshdesk-v2',
    description='A Python interface for the Freshdesk API. This is a fork of https://github.com/sjkingo/python-freshdesk',
    version='git',
    license='BSD',
    author='Sam Kingston, Asghar Khan',
    author_email='sam@sjkwi.com.au, asghar@asgharkhan.uk',
    description='An API for the Freshdesk helpdesk',
    url='https://github.com/i-ghost/python-freshdesk',
    install_requires=['requests', 'python-dateutil'],
    packages=['freshdesk'],
    test_suite='nose.collector',
    tests_require=['nose']
)
