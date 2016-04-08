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
Subsystem used for abstracting how payload data is acquired from its source
location.

Examples include cloning a Git repository, or fetching and extracting a
tarball from a web server.
"""

from __future__ import absolute_import, print_function, unicode_literals

import abc
import six

from vortex.compat import import_module


class AcquisitionError(Exception):
    """
    Problems raised during payload acquisition.
    """


@six.add_metaclass(abc.ABCMeta)
class Acquirer(object):
    """
    Abstract base class for acquisition methods.

    Various factory methods are provided in order to register and locate
    concrete sub-classes.
    """
    __registered = {}

    @classmethod
    def factory(cls, method, section):
        """
        Find and configure an acquirer.

        Locates a registered sub-class of :class:`Acquirer` by the given
        `method` name, then returns an instance of it configured using the
        given `section`.

        The `method` argument is expected to be a Python module name
        containing a sub-class of :class:`Acquirer`. If the method name does
        not contain any dots (``.``), the prefix ``vortex.acquirer.`` is
        prepended. For example, the acquirer method ``git`` causes the
        ``vortex.acquirer.git`` module to be loaded.

        The located class is then instantiated with the given `section` passed
        to the constructor as its only argument. The resulting object is
        returned.
        """
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
        """
        Function used to register a new :class:`Acquirer` sub-class.

        This is expected to be used as a decorator on classes implementing an
        acquisition method. For example::

            @Acquirer.register
            class MyAcquirer(Acquirer):
                ...

        Acquirer sub-classes are registered using their containing module name
        as a lookup key; the class name is ignored. The module name alone is
        used to look up sub-classes in the :meth:`factory` method.

        .. note:: Only one Acquirer sub-class may be registered per module.
        """
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
        """
        Configure this acquirer based on settings from the vortex
        configuration.

        It is intended that sub-classes use this method in order to call
        :meth:`vortex.config.VortexConfiguration.absorb` with arguments that
        are appropriate for the particular implementation.

        .. note:: This is an *abstract method* and **must** be implemented by
            sub-classes.
        """

    @abc.abstractmethod
    def acquire_into(self, directory):
        """
        Perform the resource acquisition into the given directory.

        Sub-classes should implement the actual resource acquisition in this
        method. They should use the configuration obtained in :meth:`configure`
        and do what they need to do such that the given `directory` is
        populated with data from the configured source.

        .. note:: This is an *abstract method* and **must** be implemented by
            sub-classes.
        """
