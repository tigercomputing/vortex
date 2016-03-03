# -*- coding: utf-8 -*-
#
# Copyright © 2015  Tiger Computing Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, print_function, unicode_literals

import collections
import platform
import sys

try:
    from importlib import import_module
except ImportError:
    # for Python 2.6
    def import_module(name, package=None):
        if name.startswith('.'):
            raise NotImplementedError('Relative import not supported')
        __import__(name)
        return sys.modules[name]


_PY3 = sys.version_info[0] == 3
_STRING_TYPES = (str,) if _PY3 else (basestring,)  # noqa

_REQUIRE_MODULES = {
    'six': {
        'centos': 'python-six',
        'debian': 'python3-six' if _PY3 else 'python-six',
        'redhat': 'python-six',
        'ubuntu': 'python3-six' if _PY3 else 'python-six',
    },
}


class EnvironmentException(Exception):
    """Errors caused by environmental factors."""
    pass


def _check_prerequisites():
    """
    Validate the running environment for basic features that would make it
    unviable to run at all.
    """
    PY_VER_STRING = 'Vortex requires Python 2.6+ or Python 3.3+'

    # Check for Python 2.6+
    if sys.version_info < (2, 6):
        raise EnvironmentException(PY_VER_STRING)

    # If running on Python 3, make sure we are on 3.3+
    if sys.version_info >= (3, 0) and sys.version_info < (3, 3):
        raise EnvironmentException(PY_VER_STRING)

    # We make lots of assumptions that we're running on Linux
    if platform.system() != 'Linux':
        raise EnvironmentException(
            "Vortex supports Linux only; we seem to be running on {sys}"
            .format(sys=platform.system()))

# Run our pre-requisite checks as soon as possble
_check_prerequisites()

# Get some basic information about the running system for later use
(_dist_name, _dist_ver, _dist_id) = platform.linux_distribution(
    full_distribution_name=0)


def install_package(package, name=None):
    """
    Helper to install a package on the system.

    Uses standard system packaging tools such as ``apt-get`` or ``yum`` to
    install packages on the local system.

    The ``package`` argument may be a string, list or dictionary. When it is a
    string, the value is passed to the system packaging tools as-is. When it is
    a string, each element in the list is assumed to be a package name and the
    tools are asked to install all the listed packages. When the value is a
    dictionary, the keys are expected to be short distribution names (as per
    :func:`platform.linux_distribution` with ``full_distribution_name=0``):
    when matched against the running system, the value of the entry (which may
    be a dictionary or list) is passed to the packaging tools.
    """
    if name is None:
        name = str(package)

    if isinstance(package, collections.Mapping):
        # Extract the package name(s) for this distribution
        try:
            package = package[_dist_name]
        except KeyError:
            raise EnvironmentException(
                "Don't know how to install {pkg} on {dist}".format(
                    pkg=name, dist=_dist_name))

    if isinstance(package, _STRING_TYPES):
        # Turn a single string into a list
        package = [package]

    # FIXME TODO XXX: implement this code
    raise NotImplementedError()


def check_modules(install=False):
    """
    Check for the presence of various required modules.

    If the ``install`` parameter is ``True``, an attempt will be made to
    install missing modules using :func:`install_package`. Any available
    required modules will be loaded into the running process as a side-effect
    of running this function.
    """
    missing = set()

    # Try to load all the modules in our required set. If we fail, add the
    # missing modules to the missing set.
    for module in _REQUIRE_MODULES:
        try:
            import_module(module)
        except ImportError:
            missing.add(module)

    # Have we already got all the modules? Great!
    if not missing:
        return

    # Have we been asked to install the missing ones?
    if not install:
        raise EnvironmentException(
            "Required Python modules are missing: {modules}".format(
                modules=", ".join(sorted(missing))))

    # Now try to install the missing modules
    for module in missing:
        install_package(_REQUIRE_MODULES[module], module)

    # Re-check all the modules
    missing.clear()
    for module in _REQUIRE_MODULES:
        try:
            import_module(module)
        except ImportError:
            missing.add(module)

    if not missing:
        return

    # We failed to install the modules :-(
    raise EnvironmentException(
        "Required Python modules could not be installed: {modules}".format(
            modules=", ".join(sorted(missing))))
