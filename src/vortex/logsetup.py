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
Helper module used to configure the Python :mod:`logging` framework for Vortex.

The following configuration options are *optional*:

``[logging].console`` = ``INFO``
   The log level for output that is sent to the console (e.g.
   :data:`sys.stderr`). May be any of the pre-defined log levels from the
   :mod:`logging` module or ``DISABLED`` meaning no logging is produced.

``[logging].syslog`` = ``DISABLED``
   The log level for output that is sent to syslog. May be any of the
   pre-defined log levels from the :mod:`logging` module or ``DISABLED``
   meaning no logging is produced.

``[logging].syslog_facility`` = ``user``
   The syslog facility used when sending messages to syslog. Must be one of the
   facilities named in :data:`vortex.syslog.FACILITY_NAMES`. Note that the
   syslog severity used corresponds to the priority of the message sent to the
   :mod:`logging` framework.

Additionally, the default ``console`` log level may be set using the
``VORTEX_CONSOLE`` environment variable. This is useful for debugging early
stages of the Vortex runtime before the configuration file has been loaded.
"""

from __future__ import absolute_import, print_function, unicode_literals

import logging
import os
import vortex
import vortex.syslog


#: Default values used unless overridden by the configuration
defaults = {
    'console': 'INFO',
    'syslog': 'DISABLED',
    'syslog_facility': 'user',
}

# Set up the "DISABLED" special log level we use
logging.DISABLED = 1000
logging.addLevelName(logging.DISABLED, 'DISABLED')

#: Common log formatter for console and syslog
formatter = logging.Formatter('[%(name)s] %(message)s')

#: Log handler for sending logs to standard error
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(formatter)

#: Log handler for sending logs to syslog
syslogHandler = vortex.syslog.SyslogHandler(ident='vortex')
syslogHandler.setFormatter(formatter)


def _numeric_level(loglevel):
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    return numeric_level


def _configured_level(config, option):
    try:
        return _numeric_level(config[option])
    except ValueError:
        return _numeric_level(defaults[option])


def _setup_handler(handler, config, option):
    logger = vortex.logger
    level = _configured_level(config, 'console')

    if level != logging.DISABLED:
        handler.setLevel(level)
        logger.addHandler(handler)

        # Set the logger's level to the lowest of all the handlers' levels
        if not logger.level or logger.level > level:
            logger.setLevel(level)
    else:
        logger.removeHandler(handler)


def configure(cfg):
    """
    Configure logging for Vortex.

    Uses the configuration from `cfg` (which should be an instance of
    :class:`vortex.config.VortexConfiguration`) to set up the Python
    :mod:`logging` framework. `cfg` may be `None`, in which case logging will
    be configured using default values.

    This function may be called multiple times, causing the logging framework's
    configuration to be adjusted in accordance with the desired configuration.
    """
    # Take a copy of our defaults so we don't change the defaults when we pick
    # up the user configuration.
    config = dict(defaults)

    # Check for VORTEX_CONSOLE environment variable
    try:
        config['console'] = os.environ['VORTEX_CONSOLE']
    except KeyError:
        pass

    # Extract any user configuration
    if cfg is not None:
        for option in defaults:
            if cfg.has_option('logging', option):
                config[option] = cfg.get('logging', option)

    # Adjust log levels on our handlers
    vortex.logger.setLevel(logging.NOTSET)
    _setup_handler(consoleHandler, config, 'console')
    _setup_handler(syslogHandler, config, 'syslog')

    # Adjust syslog facility
    try:
        syslogHandler.facility = vortex.syslog.facility(
            config['syslog_facility'])
    except ValueError:
        syslogHandler.facility = vortex.syslog.facility(
            defaults['syslog_facility'])
