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
    def configure(self):
        required = [
            'repository',
        ]
        defaults = {
            'revision': 'master',
        }

        # Validate the configuration and absorb the values into this object
        cfg.absorb(self, self.section, required, defaults)

    def acquire_into(self, directory):
        print("Acquiring Git repo {repo} rev {rev} into {dir}".format(
            dir=directory, repo=self.repository, rev=self.revision))
