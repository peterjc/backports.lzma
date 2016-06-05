# This file is part of a backport of 'lzma' included with Python 3.3,
# exposed under the namespace of backports.lzma following the conventions
# laid down here: http://pypi.python.org/pypi/backports/1.0
# Backports homepage: http://bitbucket.org/brandon/backports

try:
    # This is a workaround for setuptools that we'll use *if* it is present
    __import__('pkg_resources').declare_namespace(__name__)
except ImportError:
    # Otherwise, use the stdlib way defined in this rejected pep
    # http://www.python.org/dev/peps/pep-0382/
    from pkgutil import extend_path
    __path__ = extend_path(__path__, __name__)
