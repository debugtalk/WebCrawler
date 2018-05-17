#encoding: utf-8
import os
import re
from setuptools import setup, find_packages

# parse version from webcrawler/__init__.py
with open(os.path.join(os.path.dirname(__file__), 'webcrawler', '__init__.py')) as f:
    version = re.compile(r"__version__\s+=\s+'(.*)'", re.I).match(f.read()).group(1)

with open('README.md') as f:
    long_description = f.read()

setup(
    name='webcrawler',
    version=version,
    description='A simple web crawler, mainly targets for link validation test.',
    long_description=long_description,
    author='Leo Lee',
    author_email='mail@debugtalk.com',
    url='https://github.com/debugtalk/webcrawler.git',
    license='MIT',
    packages=find_packages(exclude=['tests']),
    package_data={
        'webcrawler': ['default_config.yml'],
    },
    keywords='diff compare',
    install_requires=[
        'termcolor',
        'pyyaml',
        'requests-html'
    ],
    classifiers=[
        'Programming Language :: Python :: 3.6'
    ],
    entry_points={
        'console_scripts': [
            'webcrawler=webcrawler:main'
        ]
    }
)
