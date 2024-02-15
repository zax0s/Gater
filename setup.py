from setuptools import setup, find_packages

setup(
    name='ListModeGater',
    version='0.1',
    description='Creates gated list-mode file for castor-recon',
    packages=find_packages(),
    install_requires=[
    'numpy>=1.15.4'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ],
    entry_points={
        'console_scripts': [
            'ListModeGater=ListModeGater.ListModeGater:main',
        ],
    },
)