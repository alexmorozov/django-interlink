#!/usr/bin/env python
# -*- coding: utf-8 -*-


from setuptools import setup, find_packages


with open('README.rst') as readme_file:
    readme = readme_file.read()

requirements = [
    'django>=1.8,<1.11',
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='interlink',
    version='0.0.2',
    description=('Boost website\'s SEO and UX by creating internal links '
                 'in Django.'),
    long_description=readme + '\n\n',
    author="Alex Morozov",
    author_email='alex@morozov.ca',
    url='https://github.com/alexmorozov/django-interlink',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='interlink',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests.test_app.tests',
    tests_require=test_requirements
)
