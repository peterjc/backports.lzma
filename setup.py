#!/usr/bin/python -u
#
# Python Bindings for XZ/LZMA backported from Python 3.3.0
#
# This file copyright (c) 2012 Peter Cock, p.j.a.cock@googlemail.com
# See other files for separate copyright notices.

import sys, os
from warnings import warn

from distutils import log
from distutils.command.build_ext import build_ext
from distutils.core import setup
from distutils.extension import Extension

packages = ["backports", "backports.lzma"]
home = os.path.expanduser("~")
extens = [Extension('backports/lzma/_lzma',
                    ['backports/lzma/_lzmamodule.c'],
                    libraries = ['lzma'],
                    include_dirs = [os.path.join(home, 'include')],
                    library_dirs = [os.path.join(home, 'lib')]
                    )]

descr = "Backport of Python 3.3's 'lzma' modoule for XZ/LZMA compressed files."
long_descr = """This is a backport of the 'lzma' module included in Python 3.3 or later
by Nadeem Vawda and Per Oyvind Karlsen, which provides a Python wrapper for XZ Utils
(aka LZMA Utils v2) by Igor Pavlov.

In order to compile this, you will need to install XZ Utils from http://tukaani.org/xz/
"""

if sys.version_info < (2,6):
    sys.stderr.write("ERROR: Python 2.5 and older are not supported, and probably never will be.\n")
    sys.exit(1)

setup(
    name = "backports.lzma",
    version = "0.0.1b",
    description = descr,
    author = "Peter Cock, based on work by Nadeem Vawda and Per Oyvind Karlsen",
    author_email = "p.j.a.cock@googlemail.com",
    url = "https://github.com/peterjc/backports.lzma",
    license='3-clause BSD License',
    keywords = "xy lzma compression decompression",
    long_description = long_descr,
    classifiers = [
        #'Development Status :: 5 - Production/Stable',
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        #'Operating System :: OS Independent',
        'Topic :: System :: Archiving :: Compression',
    ],
    packages = packages,
    ext_modules = extens,
    cmdclass = {
        'build_ext': build_ext,
    },
)
