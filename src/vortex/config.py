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

import os

from six import PY3
from six.moves.configparser import SafeConfigParser


class ConfigurationError(Exception):
    pass


class VortexConfiguration(SafeConfigParser, object):
    def __init__(self, filename=None):
        super(VortexConfiguration, self).__init__()
        self.__filename = None

        if filename:
            self.read_config(filename)

    def read_config(self, filename):
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

        self._validate_config()

    def _validate_config(self):
        required = [
            ('bootstrap', 'source'),
        ]

        for (section, option) in required:
            if not self.has_option(section, option):
                raise ConfigurationError(
                    "{ini}: missing required option [{sec}].{opt}.".format(
                        ini=self.__filename, sec=section, opt=option))

# Configuration file path
VORTEX_INI = '/etc/vortex.ini'
VORTEX_INI = os.environ.get('VORTEX_INI', VORTEX_INI)

# Load the configuration
cfg = VortexConfiguration(VORTEX_INI)
