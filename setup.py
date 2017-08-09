# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

find_packages()
setup(
    name='stf-utils',
    maintainer='2GIS',
    maintainer_email='autoqa@2gis.ru',
    packages=find_packages(),
    package_data={
        'stf_utils': [
            'config/*.ini'
        ],
    },
    version='0.1.0',
    entry_points={
        'console_scripts': [
            'stf-connect = stf_utils.stf_connect.stf_connect:run',
            'stf-record = stf_utils.stf_record.stf_record:run',
        ],
    },
    install_requires=[
        'six==1.10.0',
        'requests==2.10.0',
        'asyncio==3.4.3',
        'autobahn==0.13.0',
    ],
    license='MIT',
    description='',
    long_description='',
    url='https://github.com/2gis/stf-utils'
)

