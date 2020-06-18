# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='testgenerator',
    version='0.0.1',
    description='',

    packages=find_packages(include=['testgenerator', 'testgenerator.*']),


    # scripts=['scripts/testgenerator'],

    entry_points={
        'console_scripts': [
            'testgenerator=testgenerator.commands:cli'
        ]
    },
    install_requires=[
        'flask',
        'click'    
    ]
)
