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
Vortex provides a means to specialise a bare Linux cloud instance according to
a version-controlled configuration.

It is designed to be bootstrapped from an `Amazon AWS`_ instance's `User Data`_
field using `Cloud-Init`_. From there it configures your instance according to
your configuration (for example using `Puppet`_).

.. _Amazon AWS: http://aws.amazon.com/
.. _User Data:
    http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html
.. _Cloud-Init: https://launchpad.net/cloud-init
.. _Puppet: https://puppetlabs.com/
"""

from __future__ import absolute_import, print_function, unicode_literals

# NB important side-effect: this import runs pre-requisite checks.
from vortex.environment import check_modules


def stage2():
    """
    Main entry-point for Stage 2 of the bootstrapping process.

    This function is called by the :mod:`vortex.bootstrap` module once the main
    :mod:`vortex` package is available. This checks that the environment is set
    up correctly (using :func:`vortex.environment.check_modules` with
    ``install=True``), then starts the deployment process by calling
    :meth:`vortex.runtime.Runtime.run`.
    """
    # Make sure we have all the modules we require
    check_modules(install=True)

    # Now that we have the required modules, we can import our main runtime and
    # get started
    from vortex.runtime import runtime
    runtime.run()
