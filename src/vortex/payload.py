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
import os.path

from vortex.acquirer import Acquirer
from vortex.config import cfg
from vortex.runtime import runtime


class Payload(object):
    @classmethod
    def configured_payloads(cls):
        """
        Returns a list of all configured payloads.

        Returns a list of Payload objects, one for each configured payload in
        the configuration file. The ordering from the configuration file is
        preserved if we are running a supported Python version (2.7+)
        """
        try:
            return cls.__configured_payloads
        except AttributeError:
            pass

        # Keep a separate set of names and a list of payloads: this helps to
        # preserve ordering on Python 2.7+.
        payload_names = set()
        payloads = []

        for section in cfg.sections():
            # Skip any non-payload sections
            if not section.startswith('payload:'):
                continue

            # Extract the payload name
            name = section.split(':')[1]

            # If we end up with a blank name, or we already have this payload
            # all configured, skip this section
            if not name or name in payload_names:
                continue

            # New payload: configure it
            payload_names.add(name)
            payloads.append(cls(name))

        cls.__configured_payloads = payloads
        return cls.__configured_payloads

    def __init__(self, name):
        super(Payload, self).__init__()
        self.name = name
        self._configure()

    def _configure(self):
        required = [
            'acquire_method',
        ]
        defaults = {
            'environment': 'development',
        }

        # Validate the configuration and absorb the values into this object
        cfg.absorb(self, 'payload:' + self.name, required, defaults)

    @property
    def directory(self):
        # We'll put all our payloads into a directory within our temporary
        # directory, so figure out its path and make sure the directory exists
        # before we use it.
        payloads = os.path.join(runtime.tmpdir, 'payloads')
        if not os.path.isdir(payloads):
            os.mkdir(payloads)

        # Note: the payload directory itself is not automatically created
        return os.path.join(payloads, self.name)

    def acquire(self):
        # FIXME TODO
        print("Acquiring payload {name}".format(name=self.name))

        acquirer = Acquirer.factory(
            self.acquire_method,
            "payload:{name}:{method}".format(
                name=self.name, method=self.acquire_method))

        acquirer.acquire_into(self.directory)

    def deploy(self):
        # FIXME TODO
        print("Deploying payload {name}".format(name=self.name))
