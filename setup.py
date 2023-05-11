from setuptools import setup, find_packages
setup(
    name='file-validator',
    version='1.0.0',
    description='A utility for validating files before ingestion',
    author='Vinayak',
    author_email='in.vinayak@gmail.com',
    packages=find_packages(),
    install_requires=[
        'pandas==1.4.0',
        'pydantic==1.8.2',
        'regex==2021.4.4',
        'loguru==0.5.3'
    ],
    entry_points={
        'console_scripts': [
            'file-validator = file_validator.main:main'
        ]
    },
)
