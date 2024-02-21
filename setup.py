#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name='echo-crafter',
    version='0.1.0',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'microphone_listen = echo_crafter.listener.listener_with_wake_word:main',
            'transcripts_collect = echo_crafter.listener.socket_read:main'
        ]
    }
)
