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
import re
import json
import celery
import logging

from cu.configs.configs \
    import read_config_wrt_git

from cu.utils.redis.dictionary \
    import Redis_Dictionary

from cu.storage.files_lrucache \
    import Files_LRUCache
from cu.storage.local_io.files \
    import LOCALIO_Files


def _set_localmount(configs, allowed_remote):
    if 'localmount_' not in allowed_remote:
        return allowed_remote, None

    res = {'localmount_{}'.format(x): \
           configs['localmount_'][x]\
           for x in list(configs['localmount_'])}

    remotes = [x for x in allowed_remote if x != 'localmount_']
    remotes += list(res.keys())

    return remotes, res


_GITROOT, CONFIGS = read_config_wrt_git()

CONFIGS['git_root'] = _GITROOT

CONFIGS['logs_path'] = os.path.join(_GITROOT, CONFIGS['logging']['path'])
os.makedirs(CONFIGS['logs_path'], exist_ok = True)

CONFIGS['webserver_logs_kwargs'] = {
    'filename': os.path.join(CONFIGS['logs_path'],
                             'webserver.log'),
    'level': CONFIGS['logging']['level'],
    'format': "[%(asctime)s] %(levelname)s: %(filename)s::%(funcName)s %(message)s"}

CONFIGS['broker_url'] = '{name}://{url}:{port}/{db}'.format\
    (name = CONFIGS['broker']['name'],
     url = CONFIGS['broker']['url'],
     port = CONFIGS['broker']['port'],
     db = CONFIGS['broker']['db'])

CELERY_APP = celery.Celery\
    (broker=CONFIGS['broker_url'],
     backend=CONFIGS['broker_url'],
     task_track_started=True,
     result_expires = CONFIGS['broker']['result_expires'],
     enable_utc = True)
CELERY_APP.autodiscover_tasks(['cu.cache','cu.webserver'])

ALLOWED_REMOTE = CONFIGS['remotestorage']['use_remotes']
ALLOWED_REMOTE, _LOCAL_STORAGE_ROOTS = \
    _set_localmount(CONFIGS, ALLOWED_REMOTE)
DEFAULT_REMOTE = CONFIGS['remotestorage']['default']

CACHE_ODIR = CONFIGS['localcache']['path']


def get_Tasks_Queues():
    return Redis_Dictionary\
        (name = 'celery_utils_tasks_queue',
         redis_url = CONFIGS['broker_url'],
         expire_time = CONFIGS['broker']['result_expires'])


def get_RESULTS_CACHE():
    return Files_LRUCache\
        (path = CACHE_ODIR,
         maxsize = int(CONFIGS['localcache']['limit']))


def get_LOCAL_STORAGE(remotetype):
    if not re.match('localmount_.*', remotetype):
        raise RuntimeError\
            ("remotetype = {} does not match localmount_*")

    return LOCALIO_Files(root = _LOCAL_STORAGE_ROOTS[remotetype],
                         redis_url = CONFIGS['broker_url'])
