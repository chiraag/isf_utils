from setuptools import setup, find_packages

setup(
    name='isf',
    version='0.1',
    url='https://github.com/chiraag/isf_utils',
    author='Chiraag Juvekar',
    author_email='chiraag.juvekar@gmail.com',
    description='Utilities to parse isf binaries from Textronix scopes',
    packages=find_packages(),    
    install_requires=[
        'numpy >= 1.17.2',
        'scipy >= 1.3.1',
        'bokeh >= 1.3.4',
        'fire >= 0.2.1',
    ],
)