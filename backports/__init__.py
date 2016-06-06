# This file is part of a backport of 'lzma' included with Python 3.3,
# exposed under the namespace of backports.lzma following the conventions
# laid down here: http://pypi.python.org/pypi/backports/1.0
# Backports homepage: http://bitbucket.org/brandon/backports

# A Python "namespace package" http://www.python.org/dev/peps/pep-0382/
# This always goes inside of a namespace package's __init__.py

try:
    import pkg_resources
    pkg_resources.declare_namespace(__name__)
except ImportError:
    import pkgutil
    __path__ = pkgutil.extend_path(__path__, __name__)
