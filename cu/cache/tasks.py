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

from cu.decorators \
    import task

from cu.storage.remotestorage_path \
    import RemoteStoragePath, is_remote_path

from cu.utils.files \
    import move_file

from cu.exceptions \
    import FILE_DISAPPEARED


def _ofn(meta_fn, ofn):
    if not meta_fn.in_storage():
        raise FILE_DISAPPEARED('{}_meta has disappeared!')

    serialise = meta_fn.get_locally(True)['serialise']
    return str(RemoteStoragePath(ofn, serialise = serialise))


def _save_meta(data, ofn):
    return data


def _cache_meta(data, meta_fn, cache_kwargs):
    from cu.cache.cache import cache_fn
    cache_fn(return_type=meta_fn.serialisation,
             ofn_arg='ofn', **cache_kwargs)(_save_meta)\
             (data = data, ofn = meta_fn.path)


@task(cache = False, get_args_locally = False)
def call_fn_cache(result, ofn, call_serialiser, cache_kwargs):
    ofn = RemoteStoragePath(ofn).path
    meta_fn = RemoteStoragePath\
        (ofn + '_meta', serialise = call_serialiser)

    if result is None:
        return _ofn(meta_fn, ofn)

    result_rmt = RemoteStoragePath(result)
    ofn = RemoteStoragePath\
        (ofn, serialise=result_rmt.serialisation)

    if is_remote_path(result):
        _cache_meta(data = {'serialise': ofn.serialisation},
                    meta_fn = meta_fn, cache_kwargs = cache_kwargs)
        ofn.link(result_rmt.path)
        return str(ofn)

    if not os.path.exists(result_rmt.path):
        raise FILE_DISAPPEARED\
            (f"{result_rmt.path} is not remote "
             "and not locally present!")

    # result_rmt is not a remote path, but a local one. It is assumed
    # here, that no serialisation is needed!
    move_file(result_rmt.path, ofn.path, True)
    ofn.upload()
    return str(ofn)
