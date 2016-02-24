Vortex: Operating System Compatibility
======================================

This document collates various aspects of our minimum required OS versions (per
the [Design Overview](design-overview.md) document.

Overview
--------

| Operating System | Stock Python | Python 3? | Python `six` |
| ---------------- | ------------ | --------- | ------------ |
| Amazon Linux 2014.09 | 2.6 | 3.4 (`python34`) | 1.8.0 |
| CentOS 7.0 | 2.7 | 3.3 (SCL) | 1.3.0 |
| Debian 8.0 (`jessie`) | 2.7 | 3.4 (`python3`) | 1.8.0 |
| Ubuntu 14.04 LTS (`trusty`) | 2.7 | 3.4 | 1.5.2 |
| Ubuntu 15.10 (`wily`) | TODO | TODO | TODO |

Minimum Python: 2.6.6 (Amazon Linux 2014.09)
Minimum Python `six`: 1.3.0 (CentOS 7.0)

Amazon Linux 2014.09
--------------------

RPM-based, loosely based on CentOS / Red Hat 6.x.

Pre-requisite packages:

* `redhat-lsb-core` (**early** for `lsb_release`)
* `python-six` (1.8.0)

| Command | Result |
| ------- | ------ |
| `lsb_release -s -i` | `AmazonAMI` |
| `lsb_release -s -r` | `2014.09` |
| `lsb_release -s -c` | `n/a` |
| `python -V` | `Python 2.6.9` |
| `curl -V` | `7.38.0` (abbr) |
| `wget -V` | `1.16` (abbr) |
| `gpg --version` | TODO |

Python 3.4 is available in the `python34` package.

CentOS 7.0
----------

RPM-based, based on Red Hat 7.0.

Pre-requisite packages:

* `redhat-lsb-core` (**early** for `lsb_release`)
* `python-six` (1.3.0 in 7.0)

| Command | Result |
| ------- | ------ |
| `lsb_release -s -i` | `CentOS` |
| `lsb_release -s -r` | `7.0.1406` |
| `lsb_release -s -c` | `Core` |
| `python -V` | `Python 2.7.5` |
| `curl -V` | `7.29.0` (abbr) |
| `wget -V` | not installed |
| `gpg --version` | `2.0.22` (abbr) |

Python 3.3 is available, but need SCL enabling and then Python running through
a wrapper that enables SCL. Not feasible.

Debian 8.0
----------

DEB-based.

Pre-requisite packages:

* `lsb-release` (**early** for `lsb_release`)
* `python` (maybe? in standard packages but not a minimal install)
* `python-six` (maybe? in standard packages but not a minimal install)

| Command | Result |
| ------- | ------ |
| `lsb_release -s -i` | `Debian` |
| `lsb_release -s -r` | `8.0` |
| `lsb_release -s -c` | `jessie` |
| `python -V` | `Python 2.7.9` |
| `curl -V` | not installed |
| `wget -V` | `1.16` (abbr) |
| `gpg --version` | `1.4.18` (abbr) |

Python 3.4 is available in the `python3` package.

Ubuntu 14.04 LTS
----------------

Based on Debian.

Pre-requisite packages:

* `lsb-release` (**early** for `lsb_release`; pre-installed?)

| Command | Result |
| ------- | ------ |
| `lsb_release -s -i` | `Ubuntu` |
| `lsb_release -s -r` | `14.04` |
| `lsb_release -s -c` | `trusty` |
| `python -V` | `Python 2.7.6` |
| `curl -V` | `7.35.0` (abbr) |
| `wget -V` | `1.15` (abbr) |
| `gpg --version` | `1.4.16` (abbr) |

Python 3.4 is available in the `python3` package, but appears to be includes in
standard installations.
