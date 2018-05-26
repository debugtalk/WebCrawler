#encoding: utf-8
import os
import re
from setuptools import setup, find_packages

# parse version from requests_crawler/__init__.py
with open(os.path.join(os.path.dirname(__file__), 'requests_crawler', '__init__.py')) as f:
    version = re.compile(r"__version__\s+=\s+'(.*)'", re.I).match(f.read()).group(1)

with open('README.md') as f:
    long_description = f.read()

setup(
    name='requests-crawler',
    version=version,
    description='A simple web crawler, mainly targets for link validation test.',
    long_description=long_description,
    author='debugtalk',
    author_email='mail@debugtalk.com',
    url='https://github.com/debugtalk/webcrawler.git',
    license='MIT',
    packages=find_packages(exclude=['tests']),
    package_data={},
    keywords='web crawler validation',
    install_requires=[
        'termcolor',
        'requests-html'
    ],
    classifiers=[
        'Programming Language :: Python :: 3.6'
    ],
    entry_points={
        'console_scripts': [
            'requests_crawler=requests_crawler:main'
        ]
    }
)
