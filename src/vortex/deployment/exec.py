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
import subprocess

from vortex.compat import shell_quote
from vortex.deployment import DeploymentHandler, DeploymentError
from vortex.utils import list_to_cmdline


logger = logging.getLogger(__name__)


@DeploymentHandler.register
class ExecHandler(DeploymentHandler):
    """
    ``exec`` deployment handler.

    This deployment handler can be used to run arbitrary commands or scripts.
    It can be configured in multiple ways:

    * From a YAML document or JSON file, for example (in YAML):

        .. code-block:: yaml

           ---
           exec:
             - mkdir -p /etc/myapp
             - date '+%F %T.%N' >> /etc/myapp/.deploy-stamp
             - - /usr/bin/rsync
               - -av
               - www/
               - /var/www/myapp/

    * By placing executable files (that is, files with the executable bit set)
      into the ``.vortex`` directory.

    If the command to be executed is a string (e.g. the configuration contains
    array elements that are strings), the command will be executed by pasing it
    to a shell. This emulates traditional :func:`os.system` execution, and
    means that shell syntax such as redirection and variable interpolation
    work. The first two execution examples in the YAML code block above
    demonstrate this.

    If the command is a list (or is an executable file in the ``.vortex``
    directory), the shell is bypassed and the command is executed directly. The
    first element in the list is the command to execute (the PATH variable is
    searched for unqualified commands), and each subsequent element is an
    individual argument passed verbatim to the command. Shell syntax does not
    work, and quoting or variable interpolation will be passed as-is as
    arguments to the command.

    Commands are run with an empty environment aside from the ``PATH`` variable
    (which is inherited) and the ``VORTEX_ENVIRONMENT`` variable, which
    corresponds to the ``environment`` configuration option given for the
    payload in the ``vortex.ini`` configuration.

    Standard input is connected to ``/dev/null``, while standard output and
    standard error are passed-through as-is: any command output will be seen on
    the executing console and unseen (and for example not redirected to syslog)
    by Vortex.
    """

    def configure(self, config):
        """
        Configure this deployment helper based on settings from the deployment
        configuration.

        See :meth:`vortex.deployment.DeploymentHandler.configure`.
        """
        self.commands = config

    def _runcmd(self, args):
        env = {
            'PATH': os.environ.get('PATH'),
            'VORTEX_ENVIRONMENT': self.payload.environment,
        }

        if str(args) == args:
            # If we're asked to exec a simple string, we'll call a shell to do
            # the work.
            args = ['/bin/sh', '-c', args]

        if logger.isEnabledFor(logging.DEBUG):
            debug_env = ' '.join(
                "{var}={val}".format(
                    var=shell_quote(x), val=shell_quote(env[x]))
                for x in sorted(env))
            logger.debug("Running: env -i {env} {cmd}".format(
                env=debug_env, cmd=list_to_cmdline(args)))

        with open(os.devnull, 'r') as devnull:
            p = subprocess.Popen(
                args,
                stdin=devnull, stdout=None, stderr=None,
                close_fds=True, cwd=self.payload.directory, env=env)
            ret = p.wait()

        return ret

    def deploy(self):
        """
        Perform the configured deployment step.

        See :meth:`vortex.deployment.DeploymentHandler.deploy`.
        """
        for cmd in self.commands:
            ret = self._runcmd(cmd)
            logger.debug("Exit code: {ret}".format(ret=ret))

            if ret != 0:
                raise DeploymentError(
                    "Deployment exec returned failure ({ret}): {cmd}".format(
                        ret=ret, cmd=cmd))
