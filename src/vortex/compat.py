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
Compatibility functions and wrappers.

.. py:function:: import_module(name[, package=None])

   On Python >= 2.7, this is simply a re-exported version of
   :func:`importlib.import_module`.

   On Python 2.6, where :mod:`importlib` does not exist, this provides a very
   simple wrapper around :func:`__import__` that doesn't support relative
   import. The ``package`` argument is ignored, and a
   :exc:`NotImplementedError` is raised if the ``name`` argument starts with a
   dot (``.``).

.. py:function:: shell_quote(s)

   On Python >= 3.3, this is a re-exported and renamed version of
   :func:`shlex.quote`. Otherwise, this is a re-exported and renamed version of
   :func:`pipes.quote`.
"""

from __future__ import absolute_import, print_function, unicode_literals

import sys

# IMPORTANT: All code in this file must only use the Python standard library
# modules only. In particular, one cannot assume that Six is available.

try:
    from importlib import import_module
except ImportError:
    # for Python 2.6
    def import_module(name, package=None):
        if name.startswith('.'):
            raise NotImplementedError('Relative import not supported')
        __import__(name)
        return sys.modules[name]

try:
    from shlex import quote as shell_quote  # noqa
except ImportError:
    # Undocumented but exists in Python 2.6
    from pipes import quote as shell_quote  # noqa
