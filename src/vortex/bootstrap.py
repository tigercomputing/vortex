#!/usr/bin/python
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
"""
Vortex 1st stage bootstrap functionality.

This file is a stand-alone executable Python script that is designed to be
called by the "Stage 0" bootstrap (e.g. Cloud-Init). Its tasks are to:

* Locate and parse the Vortex configuration file.
* Download the rest of Vortex from a distribution source.
* Validate the downloaded file's cryptographic signature (TODO).
* Load the downloaded Vortex package and run the next stage of the bootstrap
  process.

All of the above must be done using only the Python standard library, and must
be fully compatible with Python 2.6 or higher, and Python 3.3 or higher.

The following configuration options are *required*:

``[bootstrap].source``
   The source URI to download Vortex from. This can be any URI supported by
   Python's :mod:`urllib` (or :mod:`urllib.request` in Python 3+). The URI must
   point at a Python Egg file containing the rest of the Vortex code.

The following configuration options are *optional*:

``[bootstrap].entry`` = ``vortex:stage2``
   The entry point function to call after having downloaded the Egg file. By
   default this points at :func:`vortex.stage2`, which is used to continue the
   bootstrap process.

Some of the code in this file is made up of simpler / stripped
re-implementations of code found elsewhere in Vortex, or even from parts of
:mod:`six`.
"""

from __future__ import absolute_import, print_function, unicode_literals

# Straight module imports
import atexit
import collections
import os
import os.path
import shutil
import sys
import tempfile

# Workaround for Sphinx bug 1641. Without this kind of thing, Sphinx barfs when
# using print as a function. https://github.com/sphinx-doc/sphinx/issues/1641
try:
    import builtins
    print_ = getattr(builtins, 'print')
except ImportError:
    import __builtin__
    print_ = getattr(__builtin__, 'print')

# Imports taking care of Python 2.x => 3.x renames
try:
    from ConfigParser import SafeConfigParser
except ImportError:
    from configparser import SafeConfigParser

try:
    from urllib import urlretrieve
except ImportError:
    from urllib.request import urlretrieve

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

try:
    from importlib import import_module
except ImportError:
    # for Python 2.6
    def import_module(name, package=None):
        if name.startswith('.'):
            raise NotImplementedError('Relative import not supported')
        __import__(name)
        return sys.modules[name]

#: Path to Vortex configuration file. Can be overridden using the
#: ``VORTEX_INI`` environment variable.
VORTEX_INI = '/etc/vortex.ini'
VORTEX_INI = os.environ.get('VORTEX_INI', VORTEX_INI)

#: Parsed configuration. See :func:`read_config`.
config = SafeConfigParser()

#: Path to a temporary directory. Automatically deleted at exit (see
#: :func:`cleanup_tmpdir`).
tmpdir = tempfile.mkdtemp(prefix='vortex-')

# Configuration defaults
config.add_section('bootstrap')
config.set('bootstrap', 'entry', 'vortex:stage2')


@atexit.register
def cleanup_tmpdir():
    """
    Delete our temporary directory at exit.

    Called when the Python interpreter exits using :func:`atexit.register`.
    """
    shutil.rmtree(tmpdir)


def die(message, exit=1):
    """
    Simple wrapper to print to ``stderr`` and exit with a failure return.
    """
    print_(message, file=sys.stderr)
    sys.exit(exit)


def read_config():
    """
    Read the ``vortex.ini`` configuration file and perform sanity checks.
    """
    read = config.read(VORTEX_INI)
    if not read:
        die("{ini}: failed to read configuration file".format(ini=VORTEX_INI))

    if not config.has_option('bootstrap', 'source'):
        die("{ini}: missing required [bootstrap].source option".format(
            ini=VORTEX_INI))


def fetch_vortex():
    """
    Download the Vortex Egg file.

    Returns the full path to the downloaded file, which will be within the
    :data:`tmpdir` directory.

    .. todo:: Validate cryptographic signature.
    """
    url = config.get('bootstrap', 'source')
    o = urlparse(url)
    filename = os.path.basename(o.path)
    filepath = os.path.join(tmpdir, filename)

    urlretrieve(url, filename=filepath)

    # FIXME: validate signature

    return filepath


def execute_vortex(filepath):
    """
    Execute the downloaded egg and hand over control.
    """
    # Obtain the module name and entry function to call
    entry = config.get('bootstrap', 'entry')
    module_name, fn_name = entry.split(':', 1)

    # Import the module into the current process
    sys.path.insert(1, filepath)
    try:
        module = import_module(module_name)
    except ImportError:
        die("Failed to import module '{mod}' from Egg at {egg}".format(
            mod=module_name, egg=filepath))

    # Locate the entry point
    try:
        fn = getattr(module, fn_name)
    except AttributeError:
        die("Failed to locate entry point '{ep}' in module '{mod}'".format(
            ep=fn_name, mod=module_name))

    # Try to call into the configured entry point
    if isinstance(fn, collections.Callable):
        fn()
    else:
        die("{entry}: is not callable".format(entry=entry))


def main():
    """
    Main entry point.
    """
    read_config()
    filepath = fetch_vortex()
    execute_vortex(filepath)
    sys.exit(0)


if __name__ == '__main__':
    main()
