import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

def reqs(fname):
    with open(fname) as f:
        return f.read().splitlines()

#path to package __init__ file with version
init = os.path.join(
    os.path.dirname(__file__), 'team', '__init__.py'
)

version_line = list(
    filter(lambda l: l.startswith('VERSION'), open(init))
)[0]

def get_version(version_tuple):
    if not isinstance(version_tuple[-1], int):
        return '.'.join(
            map(str, version_tuple[:-1])
             + version_tuple[-1]
        )
    return '.'.join(map(str, version_tuple))

VERSION_TUPLE =  eval(version_line.split('=')[-1])

setup(
    name = "team.datasync",
    version = get_version(VERSION_TUPLE),
    author = "Wojtek Jakubas",
    author_email = "andrewjcarter@gmail.com",
    description = ("Images push to TeamServices module"),
    license = "BSD",
    keywords = "example documentation tutorial",
    url = "http://packages.python.org/team.datasync",
    install_requires=reqs('requirements.txt'),
    packages=['team.datasync','team.datasync.api','team.datasync.service','team.datasync.entity'],
    namespace_packages=['team'],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
)