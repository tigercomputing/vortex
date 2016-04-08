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

import contextlib
import logging
import os
import os.path

from vortex.acquirer import Acquirer, AcquisitionError
from vortex.config import cfg
from vortex.environment import install_package, runcmd


logger = logging.getLogger(__name__)


@Acquirer.register
class GitAcquirer(Acquirer):
    """
    Payload acquisition using Git_.

    .. _Git: https://git-scm.com/

    The following configuration options are *required*:

        ``repository``
           URL to the remote Git repository to clone from. The URL must be
           understood by Git.

    The following configuration options are *optional*:

        ``revision`` = ``HEAD``
           The revision to checkout from the remote repository. This may be a
           branch name, tag name, ref name, commit ID or anything else
           understood by ``git checkout``. Note that in many cases, the
           resulting payload may end up on a "detached HEAD".
    """
    #: Path to the git binary
    GIT = '/usr/bin/git'

    #: Package to install. Passed to
    #: :func:`vortex.environment.install_package` if Git needs installing.
    GIT_PKG = 'git'

    def __init__(self, section):
        super(GitAcquirer, self).__init__(section)
        self.__check_installed()

    def __check_installed(self):
        # If the executable exists, that's plenty good enough.
        if os.path.isfile(self.GIT):
            return

        install_package(self.GIT_PKG)

        if os.path.isfile(self.GIT):
            return

        raise AcquisitionError(
            "Cannot find git binary after installing the git package")

    def configure(self):
        """
        Configure this acquirer based on settings from the vortex
        configuration.

        See :meth:`vortex.acquirer.Acquirer.configure`.
        """
        required = [
            'repository',
        ]
        defaults = {
            'revision': 'HEAD',
        }

        # Validate the configuration and absorb the values into this object
        cfg.absorb(self, self.section, required, defaults)

    @contextlib.contextmanager
    def __git_helper(self, cwd):
        # We're going to run Git several times, so let's hide the complexity in
        # this context manager. It just returns a function that can mangle the
        # arguments and call runcmd() for us, then check that everything went
        # OK.
        def git_wrapper(*args):
            command = [self.GIT] + list(args)
            (ret, out) = runcmd(command, cwd=cwd)
            if ret == 0:
                return

            raise AcquisitionError("Failed to acquire Git repo {repo}".format(
                repo=self.repository), out)

        yield git_wrapper

    def acquire_into(self, directory):
        """
        Perform the resource acquisition into the given directory.

        See :meth:`vortex.acquirer.Acquirer.acquire_into`.
        """
        logger.info("Acquiring Git repo {repo} rev {rev} into {dir}".format(
            dir=directory, repo=self.repository, rev=self.revision))

        if not os.path.exists(directory):
            os.mkdir(directory)

        with self.__git_helper(directory) as git:
            git('init')
            git('remote', 'add', 'origin', self.repository)
            git('fetch', 'origin', self.revision)
            git('checkout', 'FETCH_HEAD')
