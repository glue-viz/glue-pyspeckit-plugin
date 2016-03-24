#!/usr/bin/env python

from __future__ import print_function

from setuptools import setup, find_packages

entry_points = """
[glue.plugins]
pyspeckit=pyspeckit_viewer:setup
"""

try:
    import pypandoc
    LONG_DESCRIPTION = pypandoc.convert('README.md', 'rst')
except (IOError, ImportError):
    with open('README.md') as infile:
        LONG_DESCRIPTION = infile.read()

with open('pyspeckit_viewer/version.py') as infile:
    exec(infile.read())

setup(name='glue-pyspeckit-viewer',
      version=__version__,
      description='pyspeckit viewer for glue',
      long_description=LONG_DESCRIPTION,
      url="https://github.com/glue-viz/glue-pyspeckit-plugin",
      author='Adam Ginsburg and Thomas Robitaille',
      packages = find_packages(),
      package_data={},
      entry_points=entry_points
    )
