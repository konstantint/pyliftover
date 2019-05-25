'''
Pure-python implementation of UCSC ``liftOver`` genome coordinate conversion.
Setup script.

Note that "python setup.py test" invokes pytest on the package. This checks both xxx_test modules and docstrings.

Copyright 2013, Konstantin Tretyakov.
http://kt.era.ee/

Licensed under MIT license.
'''

from setuptools import setup, find_packages

from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import sys
        import pytest  # import here, cause outside the eggs aren't loaded
        sys.exit(pytest.main(self.test_args))


setup(name='pyliftover',
      version=[ln for ln in open("pyliftover/__init__.py") if ln.startswith("__version__")][0].split('"')[1],
      description="Pure-python implementation of UCSC ``liftOver`` genome coordinate conversion.",
      long_description=open("README.rst").read(),
      classifiers=[  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3',
          'Topic :: Scientific/Engineering :: Bio-Informatics'
      ],
      platforms=['Platform Independent'],
      keywords='bioinformatics liftover genome-analysis',
      author='Konstantin Tretyakov',
      author_email='kt@ut.ee',
      url='https://github.com/konstantint/pyliftover',
      license='MIT',
      packages=find_packages(exclude=['tests', 'examples']),
      include_package_data=True,
      zip_safe=True,
      install_requires=[],
      tests_require=['pytest'],
      cmdclass={'test': PyTest},
      entry_points=''
      )
