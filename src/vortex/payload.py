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

import logging
import os
import os.path

from vortex.acquirer import Acquirer
from vortex.config import cfg
from vortex.deployment import Deployer
from vortex.environment import runcmd
from vortex.runtime import runtime
from vortex.utils import cached_property


logger = logging.getLogger(__name__)


class Payload(object):
    """
    Represents a configured application payload.

    Payloads are made up of groups of files obtained using a
    :class:`vortex.acquirer.Acquirer`, then deployed to the local system
    according to rules defined within the payload itself.

    Payloads are configured in the :class:`vortex.config.VortexConfiguration`
    file as sections named ``payload:_name_``.

    The following configuration options are *required* for each defined
    payload:

        ``acquire_method``
           The method used to acquire the payload. This value is passed
           verbatim into the :meth:`vortex.acquirer.Acquirer.factory` method's
           ``method`` parameter.

    The following configuration options are *optional*:

        ``environment`` = ``development``
           Parameter passed to the payload deployment process. This can be used
           to configure the payload for a particular environment, for example
           using different settings for a development mode compared to a
           production environment.
    """
    @classmethod
    def configured_payloads(cls):
        """
        Returns a list of all configured payloads.

        Returns a list of Payload objects, one for each configured payload in
        the configuration file. The ordering from the configuration file is
        preserved if we are running a supported Python version (2.7+).

        This method iterates the configuration searching for sections starting
        ``payload:``, and returns :class:`Payload` objects for each found
        section.
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

    @classmethod
    def call_hooks(cls, hook, method, *args):
        """
        Invokes all available hook scripts.

        Looks for hook scripts of a given name (`hook`) in all configured,
        successfully acquired, payloads then invokes them with the given method
        and any other optional arguments.

        Returns a dictionary of payload names to execution results (as produced
        by :func:`vortex.environment.runcmd`.
        """
        payloads = cls.configured_payloads()
        results = {}

        for payload in payloads:
            result = payload._call_hook(hook, method, *args)
            if result is not None:
                results[payload.name] = result

        return results

    def __init__(self, name):
        super(Payload, self).__init__()
        self.name = name
        self.acquired = False
        self.deployed = False
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

    @cached_property
    def acquirer(self):
        """
        :class:`vortex.acquirer.Acquirer` object used to acquire the payload.
        """
        section = "payload:{name}:{method}".format(
            name=self.name, method=self.acquire_method)

        # Obtain an acquirer instance for the configured acquisition method
        return Acquirer.factory(self.acquire_method, section)

    @cached_property
    def deployer(self):
        """
        :class:`vortex.deployment.Deployer` object used to deploy the payload.
        """
        return Deployer(self)

    @property
    def directory(self):
        """
        Path to a temporary holding directory into which the payload will be
        acquired.

        The directory is guaranteed *not* to exist until :meth:`acquire` is
        called. The parent directory *is* guaranteed to exist, however, so a
        simple :func:`os.mkdir` with the obtained path will be sufficient to
        create the payload directory.
        """
        # We'll put all our payloads into a directory within our temporary
        # directory, so figure out its path and make sure the directory exists
        # before we use it.
        payloads = os.path.join(runtime.tmpdir, 'payloads')
        if not os.path.isdir(payloads):
            os.mkdir(payloads)

        # Note: the payload directory itself is not automatically created
        return os.path.join(payloads, self.name)

    def acquire(self):
        """
        Acquire the payload data from its configured source.

        Uses the configured :attr:`acquirer` to obtain the payload into the
        holding :attr:`directory`.
        """
        logger.info("Acquiring payload {name}".format(name=self.name))

        self.acquirer.acquire_into(self.directory)
        self.acquired = True

    def deploy(self):
        """
        Run the payload's deployment scripts in order to deploy it.
        """
        logger.info("Deploying payload {name}".format(name=self.name))

        self.deployer.deploy()
        self.deployed = True

    def _call_hook(self, hook, method, *args):
        """
        Call a hook script resisiding within this payload.

        This method should not be used by consumers within Vortex: hook scripts
        in all payloads should be called for all hookable events, so only
        :meth:`call_hooks` should be used.
        """
        # Don't call hooks if we haven't been successfully acquired
        if not self.acquired:
            return None

        hook = os.path.join(
            self.directory, Deployer.CFG_DIRNAME, 'hooks', hook)

        # Skip unless the hook is executable (and exists, etc...)
        if not os.access(hook, os.R_OK | os.X_OK):
            return None

        script_args = [hook, method]
        script_args.extend(args)

        env = {
            'VORTEX_ENVIRONMENT': self.environment,
        }

        try:
            return runcmd(script_args, env=env, cwd=self.directory)
        except:
            return None
