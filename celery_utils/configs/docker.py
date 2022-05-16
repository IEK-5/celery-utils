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


import os
import pkgutil

from celery_utils.app \
    import CONFIGS

from celery_utils.utils.git \
    import git_root


def _write_template(ofn):
    data = pkgutil.get_data('celery_utils.configs',
                            'Dockerfile')
    with open(ofn, 'wb') as f:
        f.write(data)


def write_dockerfile(dotnew = True):
    path = os.path.join(git_root(),
                        CONFIGS['docker']['dockerfile'])

    if os.path.exists(path):
        if dotnew:
            path += ".confnew"
        else:
            raise RuntimeError('File exists and dotnew = False! {}'\
                               .format(path))

    os.makedirs(os.path.dirname(path), exist_ok = True)
    _write_template(ofn = path)
    print(f"{path}")
