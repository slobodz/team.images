"""version setup for project"""
import os

VERSION = (0,0,)
build = (0,) if not os.getenv('TRAVIS_BUILD_NUMBER') else (int(os.getenv('TRAVIS_BUILD_NUMBER')),)
__version__ = ".".join([str(x) for x in (VERSION + build)])