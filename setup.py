# TODO Exclude 'driver' from import lookup path

from setuptools import setup

setup(
    name='gamcho',
    author='Cheongyo Bahk',
    author_email='cg.bahk@gmail.com',
    packages=['gamcho'],
    # Recommended: python >= 3.7
    # TODO How to express this?
    install_requires=[
        # Do NOT add every requirement. Most helper will just use already installed version.
        'ipython',
        'pudb',
    ],
)
