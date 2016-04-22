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

from vortex.deployment import DeploymentHandler
from vortex.environment import install_package


logger = logging.getLogger(__name__)


@DeploymentHandler.register
class PackagesHandler(DeploymentHandler):
    """
    ``packages`` deployment handler.

    This deployment handler can be used to install Apt/Yum packages. The
    appropriate package manager will be used depending on what system the
    deployment is running on.

    This handler simply passes the given configuration to
    :func:`vortex.environment.install_package`. Any configuration described
    here applies to that function in general, and vice versa.

    In its simplest form, the configuration consists of a list (array) of
    package names. These will be passed to the relevant package manager for
    installation. For example:

    .. code-block:: yaml

       ---
       packages:
         - apache2
         - nodejs
         - npm
         - php5-fpm

    A more advanced mechanism is available whereby a different list of packages
    may be used depending on the *distribution* that the deployment is
    occurring on. To use this method, the configuration should be a mapping
    (dictionary, or JSON "object") where the keys are lowercase short
    distribution names (as per :func:`platform.linux_distribution` with
    ``full_distribution_name=0``, but in lowercase), and the values are arrays
    of packages relevant to that distribution. For example:

    .. code-block:: yaml

       ---
       packages:
         centos: &yumpkg
           - httpd
           - php-fpm
         debian: &aptpkg
           - apache2
           - php5-fpm
         redhat: *yumpkg
         ubuntu: *aptpkg

    Packages are installed with standard settings, without any interactivity.
    This handler offers no means to customise the package installation, for
    example by specifying a particular repository or version to install. If you
    need this level of granularity, consider using an ``exec`` instead.
    """

    def configure(self, config):
        """
        Configure this deployment helper based on settings from the deployment
        configuration.

        See :meth:`vortex.deployment.DeploymentHandler.configure`.
        """
        self.packages = config

    def deploy(self):
        """
        Perform the configured deployment step.

        See :meth:`vortex.deployment.DeploymentHandler.deploy`.
        """
        install_package(self.packages)
