Introduction
============

Python 3.3 onwards includes in the standard library module 'lzma',
providing support for working with LZMA and XY compressed files via
the XZ Utils C library (XY Utils is in a sense LZMA v2). See:

* Python's lzma - http://docs.python.org/dev/library/lzma.html
* XZ Utils - http://tukaani.org/xz/

There are some older Python libraries like PylibLZMA and PyLZMA
but these are both using LZMA Utils (not XY Utils, so they have
no XY support).

* PylibLZMA - http://pypi.python.org/pypi/pyliblzma
* PyLZMA - http://pypi.python.org/pypi/pylzma/
* LZMA Utils - http://tukaani.org/lzma/


Supported Platforms
===================

The 'lmza' module provided with Python 3.3 should work on all the
main operating systems, so in theory so too should this backport:

* Mac OS X: Tested under Python 3.1, 3.2 and 3.3
* Linux: Tested under Python 3.2 (so far)
* Windows: Untested (so far)

Support on Python 2.x would be nice to have too, but a lot more
work.


Usage
=====

The expected usage is as follows if you want to prioritise the
standard library prodived lzma if present:

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
This can happen if Python was installed from source and XY Utils
was not available. If this was a systems level Python install,
as a user you could still install XY Utils and this backport
under your own account.


Automated Testing
=================

TravisCI is being used for continuous integration testing under
32-bit Linux, currently only for Python 3.2, see:
https://travis-ci.org/peterjc/backports.lzma
