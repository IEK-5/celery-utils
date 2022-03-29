import os
import re
import json
import celery
import logging

from celery_utils.configs.configs \
    import read_config_wrt_git

from celery_utils.utils.redis.dictionary \
    import Redis_Dictionary

from celery_utils.storage.files_lrucache \
    import Files_LRUCache
from celery_utils.storage.local_io.files \
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

CONFIGS['redis_url'] = 'redis://{url}:{port}/{db}'.format\
    (url = CONFIGS['redis']['url'],
     port = CONFIGS['redis']['port'],
     db = CONFIGS['redis']['db'])

CELERY_APP = celery.Celery\
    (broker=CONFIGS['redis_url'],
     backend=CONFIGS['redis_url'],
     task_track_started=True,
     result_expires = CONFIGS['redis']['result_expires'],
     enable_utc = True)
CELERY_APP.autodiscover_tasks(['celery_utils.cache','celery_utils.webserver'])

ALLOWED_REMOTE = CONFIGS['remotestorage']['use_remotes']
ALLOWED_REMOTE, _LOCAL_STORAGE_ROOTS = \
    _set_localmount(CONFIGS, ALLOWED_REMOTE)
DEFAULT_REMOTE = CONFIGS['remotestorage']['default']

CACHE_ODIR = CONFIGS['localcache']['path']


def get_Tasks_Queues():
    return Redis_Dictionary\
        (name = 'celery_utils_tasks_queue',
         redis_url = CONFIGS['redis_url'],
         expire_time = CONFIGS['redis']['result_expires'])


def get_RESULTS_CACHE():
    return Files_LRUCache\
        (path = CACHE_ODIR,
         maxsize = int(CONFIGS['localcache']['limit']))


def get_LOCAL_STORAGE(remotetype):
    if not re.match('localmount_.*', remotetype):
        raise RuntimeError\
            ("remotetype = {} does not match localmount_*")

    return LOCALIO_Files(root = _LOCAL_STORAGE_ROOTS[remotetype],
                         redis_url = CONFIGS['redis_url'])
