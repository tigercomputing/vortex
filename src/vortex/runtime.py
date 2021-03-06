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

import atexit
import logging
import shutil
import sys
import tempfile
import vortex.logsetup

from vortex.config import cfg
from vortex.utils import cached_property


if __name__ == "__main__":
    # This is ugly, but I can't think of a sensible way of finding this value
    # out if we're just being "run" by Python.
    logger = logging.getLogger('vortex.runtime')
else:
    logger = logging.getLogger(__name__)


class Runtime(object):
    @cached_property
    def tmpdir(self):
        """
        Obtain the path to a temporary directory.

        This directory will be shared by all Vortex components, so the contents
        should be named in such a way as to avoid conflicts with other vortex
        modules. The directory will be removed when the Python interpreter
        terminates.

        Note that this is a different directory to that used by the bootstrap
        module: we make no attempt to inherit the same directory, so we'll end
        up with two "vortex-" temporary directories if we are called from the
        bootstrapper. They will both be cleaned up at exit.
        """
        # Create a new temporary directory
        tmpdir = tempfile.mkdtemp(prefix='vortex-')

        # Make sure it's removed at exit
        @atexit.register
        def _cleanup_tmpdir():
            shutil.rmtree(tmpdir)

        return tmpdir

    def run(self):
        """
        Main runtime entry point.

        Obtains and deploys the configured payloads.
        """
        # First, configure logging
        vortex.logsetup.configure(cfg)

        # Tell the user something is happening
        logger.info("Vortex runtime is starting up.")

        # Avoid circular module dependency
        from vortex.payload import Payload

        # Obtain all configured payloads
        payloads = Payload.configured_payloads()

        # No point calling hooks because no payloads have yet been acquired
        logger.info("Payload acquisition commencing.")
        # Payload.call_hooks('pre-acquire', 'payloads')

        # Acquire all the payload data first, then deploy them all as a second
        # step. This means we don't deploy anything if any of the payloads fail
        # to be acquired.
        try:
            for payload in payloads:
                payload.acquire()
        except:
            logger.critical("Payload acquisition failed. Aborting.")
            Payload.call_hooks('post-acquire', 'failed-payloads')
            sys.exit(1)

        logger.info("Payload acquisition complete.")
        Payload.call_hooks('post-acquire', 'payloads')

        logger.info("Payload deployment commencing.")
        Payload.call_hooks('pre-deploy', 'payloads')

        try:
            for payload in payloads:
                payload.deploy()
        except:
            logger.critical("Payload deployment failed. Aborting.")
            Payload.call_hooks('post-deploy', 'failed-payloads')
            sys.exit(1)

        logger.info("Payload deployment complete.")
        Payload.call_hooks('post-deploy', 'payloads')

#: Singleton instance of the Vortex Runtime class
runtime = Runtime()

if __name__ == "__main__":
    runtime.run()
