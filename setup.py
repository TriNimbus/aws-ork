#!/usr/bin/env python
import io
import os
import re
from setuptools import setup
from setuptools import find_packages
from setuptools.command.test import test as TestCommand


def find_version(filename):
    """Uses re to pull out the assigned value to __version__ in filename."""

    with io.open(filename, "r", encoding="utf-8") as version_file:
        version_match = re.search(r'^__version__ = [\'"]([^\'"]*)[\'"]',
                                  version_file.read(), re.M)
    if version_match:
        return version_match.group(1)
    return "0.0-version-unknown"


class PyTest(TestCommand):
    """TestCommand subclass to use pytest with setup.py test."""

    def finalize_options(self):
        """Find our package name and test options to fill out test_args."""

        TestCommand.finalize_options(self)
        self.test_args = ['-rx', '--cov', 'aws_ork',
            '--cov-report', 'term-missing']
        self.test_suite = True

    def run_tests(self):
        """Taken from http://pytest.org/latest/goodpractises.html."""

        # have to import here, outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        raise SystemExit(errno)


if os.path.isfile("README.rst"):
    with io.open("README.rst", encoding="utf-8") as opendescr:
        long_description = opendescr.read()
else:
    long_description = __doc__


setup(name='aws_ork',
      version=find_version("aws_ork/__init__.py"),
      description='Daemon listening on SQS for messages from an ASG',
      author='Stefan Reimer',
      author_email='stefan@trinimbus.com',
      url='https://github.com/TriNimbus/aws-ork',
      packages=find_packages(),
      data_files=[('/etc/init.d', ['dist/aws_ork']),
                  ('/etc', ['dist/aws_ork.conf'])],
      entry_points={'console_scripts': [
        "aws_ork = aws_ork:main" ]},
      install_requires=['boto3', 'salt', 'python-daemon'],
      tests_require=["pytest", "pytest-cov", "moto"],
      cmdclass={"tests": PyTest},
      long_description=long_description,
      classifiers=[
          "Development Status :: 4 - Beta",
          "Environment :: Web Environment",
          "Operating System :: POSIX",
          "Programming Language :: Python",
          "License :: OSI Approved :: MIT License",
      ])
