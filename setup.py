# -*- coding: utf-8 -*-


from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='breadboard',
    version='0.3.2',
    description='Python API client for the Breadboard API in the Zwierlein labs',
    long_description_content_type='text/markdown',
    long_description='Sorry, but twine has a bug preventing me from uploading the readme. Checkout the repo on github for a readme.',
    author='Biswaroop Mukherjee',
    author_email='mail.biswaroop@gmail.com',
    url='https://github.com/biswaroopmukherjee/breadboard-python-client',
    license='MIT license',
    packages=find_packages(exclude=('tests', 'docs'))
)
