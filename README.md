Introduction
============

Python 3.3 onwards includes in the standard library module 'lzma',
providing support for working with LZMA and XZ compressed files via
the XZ Utils C library (XZ Utils is in a sense LZMA v2). See:

* Python's lzma - http://docs.python.org/dev/library/lzma.html
* XZ Utils - http://tukaani.org/xz/

This code is a backport of the Python 3.3 standard library module 'lzma'
for use on older versions of Python where it was not included. It is
available from PyPI (released downloads only) and GitHub (repository):

* PyPI - http://pypi.python.org/pypi/backports.lzma/
* GitHub - https://github.com/peterjc/backports.lzma

There are some older Python libraries like PylibLZMA and PyLZMA
but these are both using LZMA Utils (not XZ Utils, so they have
no XZ support).

* PylibLZMA - http://pypi.python.org/pypi/pyliblzma
* PyLZMA - http://pypi.python.org/pypi/pylzma/
* LZMA Utils - http://tukaani.org/lzma/


Supported Platforms
===================

The 'lmza' module provided with Python 3.3 should work on all the
main operating systems, so in theory so too should this backport:

* Mac OS X: Tested under Python 2.6, 2.7, 3.0 to 3.4 inclusive
* Linux: Tested under Python 2.6, 2.7, 3.0 to 3.5 inclusive
* Windows: Untested (so far)

Other than some minor changes in the exceptions for some errors,
based on the unit tests everything seems to be working fine.

Support under Python 2.6 and 2.7 appears to be working in that all
the appropriate unit tests now pass. Supporting older verions of
Python 2 is probably going to be too much work.


Installation
============

First you must install the XZ Utils C library, which on a Debian
based Linux distribution can be done in one line:

    $ sudo apt-get install liblzma-dev

Otherwise do this from source, this is what I do on Mac OS X:

    $ curl -O http://tukaani.org/xz/xz-5.0.4.tar.gz
    $ tar -zxvf xz-5.0.4.tar.gz
    $ cd xz-5.0.4
    $ ./configure --prefix=$HOME
    $ make
    $ make check
    $ make install

Now you can install this 'lzma' backport. First download and
decompress the source code, or clone the github repository:

    $ git clone git://github.com/peterjc/backports.lzma.git
    $ cd backports.lzma
    $ python setup.py install
    $ cd test
    $ python test_lzma.py

To install for a specific version of Python, replace `python` (which
will use the system's default Python) in the above with a specific
version like `python2`, `python2.6` or `python3`, `python3.2`, etc.

This should find the XZ Util header file and library automatically
(and will check for a local install under your home directory).
You should now be able to import the backport from Python 3
as shown below.


Usage
=====

The expected usage is as follows if you want to prioritise the
standard library provided lzma if present:

    try:
        import lzma
    except ImportError:
        from backports import lzma
    #Then use lzma as normal, for example:
    assert b"Hello!" == lzma.decompress(lzma.compress(b"Hello!"))

Please refer to the 'lzma' documentation online:
http://docs.python.org/dev/library/lzma.html

Note that while 'lzma' should be available on Python 3.3, you
can still install the backport. This is useful for two reasons,
first testing the two act the same way, and second it is possible
that your Python installation lacks the standard library 'lzma'.
This can happen if Python was installed from source and XZ Utils
was not available. If this was a systems level Python install,
as a user you could still install XZ Utils and this backport
under your own account.

This is using the shared 'backports' namespace introduced by Brandon
Rhodes as documented here: http://pypi.python.org/pypi/backports/
and http://bitbucket.org/brandon/backports


Revisions
=========

 * v0.0.1 - January 2013
    * First public release
 * v0.0.2 - April 2013
    * Fix the seekable attribute on Python 2 (Tomer Chachamu)
    * More search paths for lib/include headers (Wynn Wilkes)
 * v0.0.3 - June 2014
    * Supports unicode filenames on Python 2 (Irving Reid)
 * v0.0.4 - September 2014
    * Declare namespace package to avoid warnings (Ralph Bean)
      (Later retracted from PyPI due to installation problems with
      ``setuptools`` versus ``distutils``, see GitHub issue #8 and #9).
 * v0.0.5 - June 2016
    * Backported fix for Python Issue 19839 to ignore non-LZMA
      trailing data (original Python 3.5.1 patch by Nadeem Vawda,
      backported by deroko, see GitHub pull request #5).
 * v0.0.6 - June 2016
   * Updated namespace packaging declaration now required by
     more recent versions of setuptools which prevented simple
     installation of v0.0.4 and v0.0.5 from PyPI.


Contributors
============

The initial Python lzma module implementation was by Per Øyvind Karlsen,
which was then rewritten by Nadeem Vawda and included with Python 3.3.
Based on this work, it was backported to also run on Python 2.6, 2.7 and
3.0, 3.1 and 3.2 by Peter Cock.

Later contributors include: Tomer Chachamu, Wynn Wilkes, Irving Reid,
Ralph Bean, Deroko


Bug Reports
===========

Please report any reproducible bugs via the GitHub issue tracker at
https://github.com/peterjc/backports.lzma/issues including details
about your operating system, version of Python, XY Utils, the lzma
backport etc. Reproducible test cases are particularly helpful.

If you can demonstrate a problem in this backport but not in the
'lzma' module included with Python 3.3 or later, then it is clearly
something we will need to fix. Any issues in the 'lzma' module as
bundled with Python 3.3 or later should be reported to the Python 
project at http://bugs.python.org instead.


Release Process
===============

After testing locally and with TravisCI (see below), new releases
are tagged in git as follows:

    $ git tag backports.lzma.vX.X.X

I then use the following to upload a new release to the Python
Packaging Index (PyPI):

    $ python setup.py register sdist upload

The update then appears on http://pypi.python.org/pypi/backports.lzma/


Automated Testing
=================

TravisCI is being used for continuous integration testing under Linux,
see https://travis-ci.org/peterjc/backports.lzma

[![Build Status](https://secure.travis-ci.org/peterjc/backports.lzma.png?branch=master)](https://travis-ci.org/peterjc/backports.lzma)
