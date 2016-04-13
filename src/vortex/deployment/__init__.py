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
Subsystem used for abstracting how payload data is deployed.
"""

from __future__ import absolute_import, print_function, unicode_literals

import abc
import json
import logging
import os
import os.path
import six
import yaml

from six import PY3
from vortex.compat import import_module
from vortex.utils import cached_property


logger = logging.getLogger(__name__)


class DeploymentError(Exception):
    """
    Problems raised during payload deployment.
    """


class Deployer(object):
    """
    FIXME
    """
    CFG_DIRNAME = '.vortex'

    def __init__(self, payload):
        super(Deployer, self).__init__()
        self.payload = payload
        self.steps = []
        self.configure()

    @cached_property
    def config_dir(self):
        """
        FIXME

        .. todo:: Should the payload configuration directory (e.g. ``.vortex``)
            be configurable?
        """
        path = os.path.join(self.payload.directory, self.CFG_DIRNAME)

        if not os.path.isdir(path):
            raise DeploymentError("Payload configuration missing")

        return path

    @cached_property
    def __config_filenames(self):
        for (_, _, filenames) in os.walk(self.config_dir):
            # Just return the sorted list of files in the config directory
            # itself, preventing iteration into child directories.
            return sorted(filenames)

    def _add_steps(self, config):
        for mod in config:
            self.steps.append(DeploymentHandler.factory(mod, config[mod]))

    def _add_json_steps(self, filename):
        path = os.path.join(self.config_dir, filename)

        if PY3:
            open_kw = {
                'encoding': 'utf-8',
            }
        else:
            open_kw = {}

        with open(path, **open_kw) as fp:
            config = json.load(fp)
            self._add_steps(config)

    def _add_yaml_steps(self, filename):
        path = os.path.join(self.config_dir, filename)

        if PY3:
            open_kw = {
                'encoding': 'utf-8',
            }
        else:
            open_kw = {}

        with open(path, **open_kw) as fp:
            for config in yaml.safe_load_all(fp):
                self._add_steps(config)

    def _add_exec_step(self, filename):
        path = os.path.join(self.config_dir, filename)

        self._add_steps({
            'exec': [path],
        })

    def configure(self):
        """
        FIXME
        """
        for f in self.__config_filenames:
            path = os.path.join(self.config_dir, f)

            if f.endswith('.json'):
                logger.debug("{p}: processing JSON step config".format(
                    p=os.path.join(self.CFG_DIRNAME, f)))
                self._add_json_steps(f)
            elif f.endswith('.yaml'):
                logger.debug("{p}: processing YAML step config".format(
                    p=os.path.join(self.CFG_DIRNAME, f)))
                self._add_yaml_steps(f)
            elif os.access(path, os.R_OK | os.X_OK):
                logger.debug("{p}: processing executable step config".format(
                    p=os.path.join(self.CFG_DIRNAME, f)))
                self._add_exec_step(f)
            else:
                logger.warn("{p}: skipping unknown file type".format(
                    p=os.path.join(self.CFG_DIRNAME, f)))

    def deploy(self):
        """
        FIXME
        """


@six.add_metaclass(abc.ABCMeta)
class DeploymentHandler(object):
    __registered = {}

    @classmethod
    def factory(cls, module, config):
        # Prepend package prefix if required
        if '.' not in module:
            module = 'vortex.deployment.' + module

        klass = cls.__locate(module)
        handler = klass(config)

        return handler

    @classmethod
    def __locate(cls, module):
        try:
            return cls.__registered[module]
        except KeyError:
            pass

        try:
            import_module(module)
        except ImportError:
            raise DeploymentError(
                "Cannot import deployment handler module {mod}.".format(
                    mod=module))

        try:
            return cls.__registered[module]
        except KeyError:
            raise DeploymentError(
                "Could not find any registered deployment modules in {mod}"
                .format(mod=module))

    @classmethod
    def register(cls, handler):
        module = handler.__module__

        if module in cls.__registered:
            raise DeploymentError(
                "Cannot register more than one deployment handler per module.")

        cls.__registered[module] = handler

        return handler

    def __init__(self, config):
        super(DeploymentHandler, self).__init__()
        self.configure(config)

    @abc.abstractmethod
    def configure(self, config):
        pass

    @abc.abstractmethod
    def deploy(self):
        pass
