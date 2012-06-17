#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import pyclap

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup



if sys.argv[-1] == "publish":
    os.system("python setup.py sdist upload")
    sys.exit()

required = []

setup(
    name='pyclap',
    version=envoy.__version__,
    description='Smart command line arguments parser',
    long_description=open('README.rst').read(),
    author='Oleg Butovich',
    author_email='oleg@butovich.com',
    url='https://github.com/swayf/pyclap',
    packages= ['pyclap'],
    install_requires=required,
    license='BSD',
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.0',
        'Programming Language :: Python :: 3.1',
    ),
)