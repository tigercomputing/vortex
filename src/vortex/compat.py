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
