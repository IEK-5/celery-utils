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
import time

from celery_utils.decorators \
    import task

from celery_utils.storage.remotestorage_path \
    import RemoteStoragePath, is_remote_path

from celery_utils.utils.files \
    import move_file

from celery_utils.exceptions \
    import NOT_IN_STORAGE


@task(cache = None, get_args_locally = False,
      autoretry_for = [NOT_IN_STORAGE])
def call_fn_cache(result, ofn, storage_type):
    if result is None:
        return ofn

    ofn = RemoteStoragePath\
        (ofn, remotetype = storage_type)
    result_rmt = RemoteStoragePath\
        (result, remotetype = storage_type)

    if os.path.exists(result_rmt.path):
        move_file(result_rmt.path, ofn.path, True)

    if is_remote_path(result):
        ofn.link(result_rmt.path)
        return str(ofn)

    ofn.upload()
    return str(ofn)
