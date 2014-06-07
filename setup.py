#!/usr/bin/env python
# coding=utf-8

from distutils.core import setup

setup(
    name='MakeWaves',
    version='0.0.1',
    author='Pete Bachant',
    author_email='petebachant@gmail.com',
    packages=['makewaves'],
    scripts=['scripts/run_makewaves.py', 'scripts/makewaves.bat'],
    url='https://github.com/petebachant/MakeWaves.git',
    license='LICENSE',
    description='Python package and app for wavemaking in the UNH tow/wave tank.',
    long_description=open('README.md').read()
)
