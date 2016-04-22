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
    Read deployment configuration and run deployment steps.

    The deployment configuration consists of YAML, JSON and executable files
    placed within a ``.vortex`` directory within the payload directory. The
    files are processed in lexical order and define the steps that need to be
    performed to deploy the payload.

    The `payload` argument should be an instance of
    :class:`vortex.payload.Payload`.
    """
    #: The name of the directory within the payload to read the deployment
    #: configuration from.
    CFG_DIRNAME = '.vortex'

    def __init__(self, payload):
        super(Deployer, self).__init__()
        self.payload = payload
        self.steps = []
        self.configure()

    @cached_property
    def config_dir(self):
        """
        Path to the configuration directory within the acquired payload.

        Returns the absolute path to the configuration directory in the
        acquired payload. Raises a :exc:`DeploymentError` if the directory does
        not exist.

        .. todo:: Should the payload configuration directory
            (:data:`CFG_DIRNAME`) be configurable?
        """
        path = os.path.join(self.payload.directory, self.CFG_DIRNAME)

        if not os.path.isdir(path):
            raise DeploymentError("Payload configuration missing")

        return path

    @cached_property
    def __config_filenames(self):
        # Returns a sorted list of filenames (not paths) in the config
        # directory.
        for (_, _, filenames) in os.walk(self.config_dir):
            # Just return the sorted list of files in the config directory
            # itself, preventing iteration into child directories.
            return sorted(filenames)

    def _add_steps(self, config):
        # Iterate the keys in config (a dict), creating a DeploymentHandler
        # instance for each, then adding them to self.steps.
        for mod in config:
            step = DeploymentHandler.factory(mod, self, config[mod])
            self.steps.append(step)

    def _add_json_steps(self, filename):
        # Parse a JSON file, passing the result to self._add_steps()
        path = os.path.join(self.config_dir, filename)

        open_kw = {'encoding': 'utf-8'} if PY3 else {}

        with open(path, **open_kw) as fp:
            config = json.load(fp)
            self._add_steps(config)

    def _add_yaml_steps(self, filename):
        # Parse a YAML file, passing each parsed document to self._add_steps()
        path = os.path.join(self.config_dir, filename)

        open_kw = {'encoding': 'utf-8'} if PY3 else {}

        with open(path, **open_kw) as fp:
            for config in yaml.safe_load_all(fp):
                self._add_steps(config)

    def _add_exec_step(self, filename):
        # Handle an executable file (a script) by synthesising an 'exec'
        # handler that executes it.
        path = os.path.join(self.config_dir, filename)

        self._add_steps({
            'exec': [[path]],
        })

    def configure(self):
        """
        Read the deployment configuration and build a sequence of steps.

        This method:

        #. Processes all JSON (``.json``), YAML (``.yaml``) and executable
           files within the ``.vortex`` configuration directory:

           * JSON files must be an "object" at the root level.
           * YAML files may consist of a number of "documents", but they must
             all be mappings.
           * Executable files are added as ``exec`` steps so that they are
             executed at that point in the sequence.
           * If multiple deployment handlers are defined within a single
             configuration file, the order in which they are executed is
             *undefined*.

        #. A :class:`DeploymentHandler` subclass is instantiated for each step.
           The key from the mappings defined in the configuration files is used
           to locate the subclass. The value is passed to the sub-class in
           order to configure that particular step.
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
        Execute the deployment steps defined in the configuration.

        This method simply iterates over the steps configured using
        :meth:`configure` and calls :meth:`DeploymentHandler.deploy` on each
        step, in order.
        """
        for step in self.steps:
            step.deploy()


@six.add_metaclass(abc.ABCMeta)
class DeploymentHandler(object):
    """
    Abstract base class for deployment handler mechanisms.
    """
    __registered = {}

    @classmethod
    def factory(cls, module, deployer, config):
        """
        Find and configure a deployment handler.

        Locates a registered sub-class of :class:`DeploymentHandler` by the
        given `module` name, then returns an instance of it configured using
        the given `config`.

        The `module` argument is expected to be a Python module name containing
        a sub-class of :class:`DeploymentHandler`. If the method name does not
        contain any dots (``.``), the prefix ``vortex.deployment.`` is
        prepended. For example, the module name ``exec`` causes the
        ``vortex.deployment.exec`` module to be loaded.

        The located class is then instantiated with the given `deployer` and
        `config` passed to the constructor as its arguments. The resulting
        object is returned.
        """
        # Prepend package prefix if required
        if '.' not in module:
            module = 'vortex.deployment.' + module

        klass = cls.__locate(module)
        handler = klass(deployer, config)

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
        """
        Function used to register a new :class:`DeploymentHandler` sub-class.

        This is expected to be used as a decorator on classes implementing a
        deployment helper. For example::

            @DeploymentHandler.register
            class MyHandler(DeploymentHandler):
                ...

        DeploymentHandler sub-classes are registered using their containing
        module name as a lookup key; the class name is ignored. The module name
        alone is used to look up sub-classes in the :meth:`factory` method.

        .. note:: Only one DeploymentHandler sub-class may be registered per
            module.
        """
        module = handler.__module__

        if module in cls.__registered:
            raise DeploymentError(
                "Cannot register more than one deployment handler per module.")

        cls.__registered[module] = handler

        return handler

    def __init__(self, deployer, config):
        super(DeploymentHandler, self).__init__()
        self.deployer = deployer
        self.payload = deployer.payload
        self.configure(config)

    @abc.abstractmethod
    def configure(self, config):
        """
        Configure this deployment handler based on settings from the deployment
        configuration.

        Additionally, the :data:`deployer` (:class:`Deployer` instance) and
        :data:`payload` (:class:`vortex.payload.Payload` instance) may be
        referenced in this method.

        .. note:: This is an *abstract method* and **must** be implemented by
            sub-classes.
        """

    @abc.abstractmethod
    def deploy(self):
        """
        Perform the configured deployment step.

        Sub-classes should implement the deployment step in this method. They
        should use the configuration obtained in :meth:`configure`.

        Additionally, the :data:`deployer` (:class:`Deployer` instance) and
        :data:`payload` (:class:`vortex.payload.Payload` instance) may be
        referenced in this method.

        .. note:: This is an *abstract method* and **must** be implemented by
            sub-classes.
        """
