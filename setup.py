#    Author: Denys Makogon
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import setuptools


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setuptools.setup(
    name='aio-orchestra',
    version='0.1',
    description='AsyncIO TOSCA orchestrator',
    long_description=read('README.rst'),
    url='https://aiorchestra.io/',
    author='Denys Makogon',
    author_email='lildee1991@gmail.com',
    packages=setuptools.find_packages(exclude=['aiorchestra.tests', ]),
    install_requires=[
        'uvloop',
        'tosca-parser',
        'requests',
        # required until new version of
        # tosca-parser will be released
    ],
    license='License :: OSI Approved :: Apache Software License',
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Developers',
        'Environment :: No Input/Output (Daemon)',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: '
        'Libraries :: Python Modules',
        'Topic :: System :: Distributed Computing',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Operating System :: MacOS',
    ],
    keywords=['orchestration', 'python', 'framework', 'asyncio'],
    platforms=['Linux', 'Mac OS-X', 'Unix'],
    tests_require=[
        'flake8==2.5.0'
        'testtools',
        'mock'
    ],
    zip_safe=True,
)
