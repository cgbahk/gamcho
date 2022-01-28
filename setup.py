# TODO Exclude 'driver' from import lookup path

from setuptools import setup, find_packages

setup(
    name='gamcho',
    author='Cheongyo Bahk',
    author_email='cg.bahk@gmail.com',
    packages=find_packages(),
    # Recommended: python >= 3.7
    # TODO How to express this?
    install_requires=[
        'ipython',
        'pandas',
        'protobuf',
        'pudb',
        'tabulate',
        'tflite',
    ],
)
