#!/usr/bin/env python
import io
import os
import re
from setuptools import setup
from setuptools import find_packages


def find_version(filename):
    """Uses re to pull out the assigned value to __version__ in filename."""

    with io.open(filename, "r", encoding="utf-8") as version_file:
        version_match = re.search(r'^__version__ = [\'"]([^\'"]*)[\'"]',
                                  version_file.read(), re.M)
    if version_match:
        return version_match.group(1)
    return "0.0-version-unknown"


if os.path.isfile("README.md"):
    with io.open("README.md", encoding="utf-8") as opendescr:
        long_description = opendescr.read()
else:
    long_description = __doc__


setup(name='aws_ork',
      version=find_version("aws_ork/aws_ork.py"),
      description='Daemon listening to SQS for messages from an ASG',
      author='Stefan Reimer',
      author_email='stefan@trinimbus.com',
      url='https://github.com/TriNimbus/aws-ork',
      packages=find_packages(),
      scripts=['aws_ork/aws_ork.py'],
      install_requires=['boto3', 'salt', 'python-daemon'],
      long_description=long_description,
      classifiers=[
          "Development Status :: 3 - Alpha",
          "Environment :: Web Environment",
          "Operating System :: POSIX",
          "Programming Language :: Python",
          "License :: OSI Approved :: MIT License",
      ])
