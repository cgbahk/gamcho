from setuptools import setup, find_packages

setup(
    name='gamcho',
    author='Cheongyo Bahk',
    author_email='cg.bahk@gmail.com',
    packages=find_packages(),
    install_requires=[
        'ipython',
        'jedi<0.18',
    ],
)
