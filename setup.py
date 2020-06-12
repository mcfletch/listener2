#!/usr/bin/env python
import os

HERE = os.path.dirname(os.path.abspath(__file__))
from setuptools import setup, find_packages

with open(os.path.join(HERE, 'README.md')) as readme_file:
    readme = readme_file.read()

requirements = []

setup_requirements = [
    'pytest-runner',
]

test_requirements = [
    'pytest>=3',
]

if __name__ == "__main__":
    setup(
        author="Mike C. Fletcher",
        author_email='mcfletch@vrplumber.com',
        python_requires='>=3.6',
        classifiers=[
            'Development Status :: 2 - Pre-Alpha',
            'License :: OSI Approved :: GNU Lesser General Public License v2 (LGPLv2)',
            'Natural Language :: English',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
        ],
        description="DeepSpeech as a (Docker) Service for IBus",
        entry_points={
            'console_scripts': [
                'listener-docker=listener.dockersetup:main',
                'listener-daemon=listener.daemon:main',
                'listener-ibus=listener.ibusengine:main',
                'listener-interpreter=listener.interpreter:main',
                'listener-debug-events=listener.eventreceiver:main',
                'listener=listener.qtgui.app:main',
                'listener-audio=listener.pipeaudio:main',
                'listener-uinput-device=listener.uinputdriver:main',
                'listener-uinput-rebuild-mapping=listener.uinputdriver:rebuild_mapping',
            ],
        },
        install_requires=requirements,
        license="LGPLv2",
        long_description=readme,
        long_description_content_type='text/markdown',
        include_package_data=True,
        keywords='DeepSpeech Speech Recognition Docker IBus',
        name='listener',
        packages=find_packages(include=['listener', 'listener.*']),
        setup_requires=setup_requirements,
        test_suite='tests',
        tests_require=test_requirements,
        url='https://github.com/mcfletch/listener',
        version='2.0.0a1',
        zip_safe=False,
    )
