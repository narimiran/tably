#!/usr/bin/env python3

from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(
    name='tably',
    version='1.0',
    author='narimiran',
    #packages=['tably'],
    scripts=['tably.py'],
    url='https://github.com/narimiran/tably.git',
    license='MIT',
    description='Python script for converting .csv data to LaTeX tables.',
    long_description=readme(),
    entry_points={'console_scripts': ['tably=tably:main']},
    keywords='python python3 command-line cli latex table csv',
        classifiers=[
        'Environment :: Console',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Text Processing :: Markup :: LaTeX',
    ],
)
