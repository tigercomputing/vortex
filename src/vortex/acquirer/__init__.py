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

import abc
import six

from vortex.compat import import_module


class AcquisitionError(Exception):
    pass


@six.add_metaclass(abc.ABCMeta)
class Acquirer(object):
    __registered = {}

    @classmethod
    def factory(cls, method, section):
        # Turn the method name into a module name
        if '.' in method:
            module = method
        else:
            module = 'vortex.acquirer.' + method

        klass = cls.__locate(module)
        acquirer = klass(section)

        return acquirer

    @classmethod
    def __locate(cls, module):
        try:
            return cls.__registered[module]
        except KeyError:
            pass

        try:
            import_module(module)
        except ImportError:
            raise AcquisitionError(
                "Cannot import acquirer module {mod}.".format(mod=module))

        try:
            return cls.__registered[module]
        except KeyError:
            raise AcquisitionError(
                "Could not find any registered acquirer modules in {mod}"
                .format(mod=module))

    @classmethod
    def register(cls, acquirer):
        module = acquirer.__module__

        if module in cls.__registered:
            raise AcquisitionError(
                "Cannot register more than one acquirer per module.")

        cls.__registered[module] = acquirer

        return acquirer

    def __init__(self, section):
        super(Acquirer, self).__init__()
        self.section = section
        self.configure()

    @abc.abstractmethod
    def configure(self):
        pass

    @abc.abstractmethod
    def acquire_into(self, directory):
        pass
