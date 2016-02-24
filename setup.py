#!/usr/bin/python
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

from setuptools import setup, find_packages

setup(
    name='vortex',
    version='0.0.1',
    description='Tool to specialise bare cloud instances',
    author='Tiger Computing Ltd',
    author_email='info@tiger-computing.co.uk',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    install_requires=[
        'six',
    ],
)
