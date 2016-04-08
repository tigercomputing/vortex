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
Provides a true syslog handler for the Python :mod:`logging` framework based on
the Python :mod:`syslog` module.
"""

from __future__ import absolute_import, print_function, unicode_literals

import logging
import syslog


#: Mapping of syslog priority names to numeric values
PRIORITY_NAMES = {
    'emerg':    syslog.LOG_EMERG,
    'alert':    syslog.LOG_ALERT,
    'crit':     syslog.LOG_CRIT,
    'err':      syslog.LOG_ERR,
    'warning':  syslog.LOG_WARNING,
    'notice':   syslog.LOG_NOTICE,
    'info':     syslog.LOG_INFO,
    'debug':    syslog.LOG_DEBUG,
}

#: Mapping of syslog facility names to numeric values
FACILITY_NAMES = {
    'kern':     syslog.LOG_KERN,
    'user':     syslog.LOG_USER,
    'mail':     syslog.LOG_MAIL,
    'daemon':   syslog.LOG_DAEMON,
    'auth':     syslog.LOG_AUTH,
    'syslog':   syslog.LOG_SYSLOG,
    'lpr':      syslog.LOG_LPR,
    'news':     syslog.LOG_NEWS,
    'uucp':     syslog.LOG_UUCP,
    'cron':     syslog.LOG_CRON,
    # 'authpriv': syslog.LOG_AUTHPRIV,  # not in syslog module
    # 'ftp':      syslog.LOG_FTP,  # not in syslog module
    'local0':   syslog.LOG_LOCAL0,
    'local1':   syslog.LOG_LOCAL1,
    'local2':   syslog.LOG_LOCAL2,
    'local3':   syslog.LOG_LOCAL3,
    'local4':   syslog.LOG_LOCAL4,
    'local5':   syslog.LOG_LOCAL5,
    'local6':   syslog.LOG_LOCAL6,
    'local7':   syslog.LOG_LOCAL7,
}

#: Mapping of :mod:`logging` priority levels to syslog priority
PRIORITY_MAP = [
    (logging.DEBUG,     syslog.LOG_DEBUG),
    (logging.INFO,      syslog.LOG_INFO),
    (logging.WARNING,   syslog.LOG_WARNING),
    (logging.ERROR,     syslog.LOG_ERR),
    (logging.CRITICAL,  syslog.LOG_CRIT),
]
# NB: Must be in *ascending* priority order!


def priority(priority):
    """
    Lookup a syslog priority level.

    Accepts either a string or integer priority level. If this is a string, the
    value is looked up in the :data:`PRIORITY_NAMES` dictionry.
    """
    if isinstance(priority, int):
        return priority
    elif str(priority) == priority:
        if priority not in PRIORITY_NAMES:
            raise ValueError("Unknown priority: %r" % priority)
        return PRIORITY_NAMES[priority]
    else:
        raise TypeError("Priority not an integer or a valid string: {}".format(
            priority))


def facility(facility):
    """
    Lookup a syslog facility number.

    Accepts either a string or integer facility. If this is a string, the value
    is looked up in the :data:`FACILITY_NAMES` dictionry.
    """
    if isinstance(facility, int):
        return facility
    elif str(facility) == facility:
        if facility not in FACILITY_NAMES:
            raise ValueError("Unknown facility: %r" % facility)
        return FACILITY_NAMES[facility]
    else:
        raise TypeError("Facility not an integer or a valid string: {}".format(
            facility))


def encode_priority(fac, pri):
    """
    Encode the facility and priority into an integer.

    Uses the :func:`priority` and :func:`facility` functions to look up the
    values based on the given parameters.
    """
    fac = facility(fac)
    pri = priority(pri)
    return fac | pri


def _map_priority(level):
    for lvl, prio in PRIORITY_MAP:
        if level <= lvl:
            return prio
    return syslog.LOG_CRIT


class SyslogFormatter(logging.Formatter):
    """
    Default custom formatter for the :class:`SyslogHandler`.
    """
    def formatException(self, ei):
        """
        Return a blank string for all exceptions.

        This avoids sending exceptions to syslog at any priority.
        """
        return ''


class SyslogHandler(logging.Handler):
    """
    Python log handler for syslog.

    This uses the Python native :mod:`syslog` module, unlike
    :class:`logging.handlers.SysLogHandler`. This means that syslog messages
    are sent to the local syslog daemon over ``/dev/log`` rather than sending
    UDP messages to localhost (or some remote host).
    """
    def __init__(self, ident=None, facility=syslog.LOG_USER,
                 options=syslog.LOG_PID, formatter=SyslogFormatter):
        logging.Handler.__init__(self)
        self.facility = facility
        self.formatter = formatter()

        if ident:
            syslog.openlog(ident, logoption=options, facility=facility)
        else:
            syslog.openlog(logoption=options, facility=facility)

    def emit(self, record):
        """
        Emit a record.
        """
        msg = self.format(record)

        # Encode the facility and priority to an integer
        prio = encode_priority(self.facility, _map_priority(record.levelno))

        syslog.syslog(prio, msg)
