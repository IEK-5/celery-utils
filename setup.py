#
# This file is part of the celery-utils (https://github.com/e.sovetkin/celery-utils).
# Copyright (c) 2022 Jenya Sovetkin.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#


import setuptools
import os
import stat


with open('README.md', 'r') as f:
    long_description = f.read()


with open('requirements.txt','r') as f:
    requirements = [x.strip() for x in f.readlines()]


def find_executable(path):
    executable = stat.S_IEXEC | stat.S_IXGRP | \
                 stat.S_IXOTH | (not stat.S_ISLNK)

    res = []
    for dp, dn, filenames in os.walk(path):
        if '.git/' in dp:
            continue

        for f in filenames:
            if not (os.stat(os.path.join(dp,f)).st_mode & executable):
                continue

            res += [os.path.join(dp,f)]

    return res


setuptools.setup(
    name='celery-utils',
    version='0.1',
    author='Evgenii Sovetkin',
    author_email='e.sovetkin@fz-juelich.de',
    description='Tools to work with celery tasks and store results in remote storage',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='git@github.com:esovetkin/celery-utils',
    packages=setuptools.find_packages(),
    package_data={'configs': ['Dockerfile']},
    include_package_data=True,
    scripts=find_executable('scripts/'),
    install_requires=requirements)
