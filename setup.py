# -*- coding: utf-8 -*-


from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='breadboard',
    version='0.1.3',
    description='Python API client for the Breadboard API in the Zwierlein labs',
    long_description=readme,
    author='Biswaroop Mukherjee',
    author_email='mail.biswaroop@gmail.com',
    url='https://github.com/biswaroopmukherjee/breadboard-python-client',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)
