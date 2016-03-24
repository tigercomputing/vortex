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
Configuration file parsing and helpers.
"""

from __future__ import absolute_import, print_function, unicode_literals

import os
import os.path
import six

from six import PY3
from six.moves.configparser import SafeConfigParser


class ConfigurationError(Exception):
    """
    Raised when an issue is detected with the Vortex configuration.
    """


class VortexConfiguration(SafeConfigParser, object):
    """
    Sub-class of the Python :class:`SafeConfigParser` to help read Vortex
    configuration files.

    If ``filename`` is not ``None``, the constructor calls :meth:`read_config`
    with the given argument.
    """
    def __init__(self, filename=None):
        super(VortexConfiguration, self).__init__()
        self.__filename = None

        if filename:
            self.read_config(filename)

    def read_config(self, filename):
        """
        Attempts to load a configuration file.

        This is a wrapper around :meth:`read_file` (on Python 3+) or
        :meth:`readfp` (on Python 2.x). This method ensures only one
        configuration file is read, and throws a :exc:`ConfigurationError` if
        called multiple times.
        """
        # Check that this isn't a 2nd attempt to load a configuration
        if self.__filename:
            raise ConfigurationError(
                "Cannot load multiple configuration files.")

        if PY3:
            # In Python3, use the new read_file() method and open the file as
            # UTF-8 explicitly.
            with open(filename, encoding='utf-8') as fp:
                self.read_file(fp, filename)
        else:
            with open(filename) as fp:
                self.readfp(fp, filename)

        # Remember the filename for later (single loading)
        self.__filename = filename

    def check_required_options(self, required):
        """
        Check whether required configuration options are present.

        Given a list of ``(section, option)`` tuples, checks that each of those
        options is present in the configuration. Raises a
        :exc:`ConfigurationError` if any of the required options are not
        present in the loaded configuration.
        """
        for (section, option) in required:
            if not self.has_option(section, option):
                raise ConfigurationError(
                    "{ini}: missing required option [{sec}].{opt}.".format(
                        ini=self.__filename, sec=section, opt=option))

    def set_default(self, section, option, value):
        """
        Sets default values for options in a given configuration section.

        If the option is already set in the given section, this method has no
        effect. Otherwise, if the section does not exist it is created, and the
        option is set to the requested value.
        """
        if self.has_option(section, option):
            return

        if not self.has_section(section):
            self.add_section(section)

        self.set(section, option, value)

    def absorb(self, target, section, required=None, defaults=None):
        """
        Helper used for absorbing configuration values into Python objects.

        If ``required`` is set, the given ``section`` is checked to ensure that
        all the options in the ``required`` list are present (using
        :meth:`check_required_options`). If set, ``required`` must be an
        iterable (e.g. a list) of strings.

        Next, if ``defaults`` is set, any options in ``defaults`` that don't
        exist in the configuration section are added to the configuration. If
        set, ``defaults`` must be a dict.

        Finally, any option named in either ``required`` or ``defaults`` is
        used to lookup values from the configuration. The options so-named are
        then set on the ``target`` object using :func:`setattr`.
        """
        # Check that any required options are present
        if required is None:
            required = []
        self.check_required_options([(section, x) for x in required])

        # Set any requested default values
        if defaults is None:
            defaults = {}
        for (option, value) in six.iteritems(defaults):
            self.set_default(section, option, value)

        # Now copy the configuration into our instance
        for option in required + list(defaults.keys()):
            value = self.get(section, option)
            setattr(target, option, value)


#: Path to Vortex configuration file. Can be overridden using the
#: ``VORTEX_INI`` environment variable.
VORTEX_INI = '/etc/vortex.ini'
VORTEX_INI = os.environ.get('VORTEX_INI', VORTEX_INI)

#: Singleton :class:`VortexConfiguration` instance. Provides a simple means to
#: access the configuration from any module by using
#: ``from vortex.config import cfg``.
cfg = VortexConfiguration()

# If the configuration file exists, read the configuration into our singleton
if os.path.exists(VORTEX_INI):
    cfg.read_config(VORTEX_INI)
