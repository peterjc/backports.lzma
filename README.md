Introduction
============

Python 3.3 onwards includes in the standard library module 'lzma',
providing support for working with LZMA and XZ compressed files via
the XZ Utils C library (XZ Utils is in a sense LZMA v2). See:

* Python's lzma - http://docs.python.org/dev/library/lzma.html
* XZ Utils - http://tukaani.org/xz/

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

* Mac OS X: Tested under Python 3.0, 3.1, 3.2 and 3.3
* Linux: Tested under Python 3.0, 3.1, 3.2 and 3.3
* Windows: Untested (so far)

Other than some minor changes in the exceptions for some errors,
based on the unit tests everything seems to be working fine.

Support under Python 2.6 and 2.7 is in progress (it now compiles but
still plenty of test failires).  Supporting older verions of Python 2
is probably going to be too much work.


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
    $ python3 setup.py install
    $ cd test
    $ python3 test_lzma.py

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


Automated Testing
=================

TravisCI is being used for continuous integration testing under 32-bit
Linux, see https://travis-ci.org/peterjc/backports.lzma

[![Build Status](https://secure.travis-ci.org/peterjc/backports.lzma.png?branch=master)](https://travis-ci.org/peterjc/backports.lzma)
