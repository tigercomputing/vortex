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

from vortex.acquirer import Acquirer
from vortex.config import cfg


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

    def acquire_into(self, directory):
        """
        Perform the resource acquisition into the given directory.

        See :meth:`vortex.acquirer.Acquirer.acquire_into`.
        """
        print("Acquiring Git repo {repo} rev {rev} into {dir}".format(
            dir=directory, repo=self.repository, rev=self.revision))
