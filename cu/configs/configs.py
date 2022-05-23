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
import pkgutil

from configparser \
    import ConfigParser

from json.decoder \
    import JSONDecodeError

from cu.utils.git \
    import git_root


_help_re = re.compile(r'__help__.*')

# _CONFIGS are used to generate default config file
_CONFIGS = dict()

_CONFIGS['app'] = dict(
    allowed_imports = ['cu.*'],
    autodiscover = ['cu'])
_CONFIGS['__help__app'] = dict(
    allowed_imports = """List of regex strings

    Those strings are matched to allow modules to be called from the
    webserver""",
    autodiscover = """List of packages that workers autodiscover"""
)

_CONFIGS['broker'] = dict(
    name='redis',
    url = 'localhost',
    port = 6379,
    db = 0,
    result_expires = 7200)
_CONFIGS['__help__broker'] = dict(
    name="""name of the broker to use.

    Allowed names so far: redis""",
    url = """ip address of the redis broker service""",
    port = """port of the redis broker""",
    db = """which db to use. should be a number between 0 and 15""",
    result_expires = """expiration time (in seconds) for stored task results

    This just ensures that dangling items disapper with time and do
    not clobber the memory.""")

_CONFIGS['worker'] = dict(
    workers = 2,
    queues = 'celery',
    max_memory = 2097152)
_CONFIGS['__help__worker'] = dict(
    workers = """maximum number of workers on node

    Note workers are autoscale down to 0, when not used
    """,
    queues = """comma separated list of queues

    leave the 'celery' queue, if you want to receive tasks that have
    no 'queue' specification

    Using queues one can make tasks to be executed on workers with
    specific hardware""",
    max_memory = """Maximum amount of resident memory (in KiB)

    If the worker consumes more than this limit, it is being replaced
    after child process is done. This helps to prevent memory leaks
    caused by children""")

_CONFIGS['localcache'] = dict(
    path = 'data/results_cache',
    limit = 10)
_CONFIGS['__help__localcache'] = dict(
    path = """path where local data is stored

    The path is relative to the git root.
    """,
    limit = """maximum size of local cache in GB

    Local cache implement least-recently-used (LRU) eviction policy.
    """)

_CONFIGS['remotestorage'] = dict(
    use_remotes = ["localmount_"],
    default = 'localmount_dir')
_CONFIGS['__help__remotestorage'] = dict(
    use_remotes = """Specify which remotes storage to use

    'localmount_' indicates a local directory.  For that a
    configuration section should exists that contains directories
    location. For instance, for 'localmount_dir1' a key 'dir1' in
    'localmount_' should exist specifying location of the directory.

    Each 'localmount_' storage directory should contain a file
    'localio.sanity'. This file is used to verify, that some node
    didn't lose its storage.

    This configuration is read by the process, when one is looking for
    a file in a remote storage.

    Other remote storage are yet to be implemented.""",
    default = """Default remote storage to use""")

_CONFIGS['localmount_'] = dict(
    dir = '/data/dir')
_CONFIGS['__help__localmount_'] = dict(
    dir = """Path for 'localmount_dir' remote storage""")

_CONFIGS['webserver'] = dict(
    host = '0.0.0.0',
    port = 8123,
    workers = 2,
    max_requests = 100,
    timeout = 20,
    uploads_dir = 'uploads')
_CONFIGS['__help__webserver'] = dict(
    host = """ip address for a webserver to listen requests to""",
    port = """port for a webserver to listen requests to""",
    workers = """number of workers for a webserver""",
    max_requests = """maximum number of requests before webserver gives up""",
    timeout = """timeout for a webserver request""",
    uploads_dir = """directory where uploads are stored

    The directory is resolved relative to
    CONFIGS['localcache']['path']""")

_CONFIGS['logging'] = dict(
    path = 'data/logs',
    level = 'INFO',
    logrotate = 'data/configs/logrotate.conf')
_CONFIGS['__help__logging'] = dict(
    path = """path for storing logs""",
    level = """level of log messages""",
    logrotate = """logrotate.conf file path

    logrotate is called from the git root directory""")

_CONFIGS['flower'] = dict(
    port = 5555)
_CONFIGS['__help__flower'] = dict(
    port = """port to use for the flower service""")


_CONFIGS['docker'] = dict(
    name = 'cu',
    registry = [],
    mounts = ["data"],
    ports = {'flower': ['docker0:5555','-:8124'],
             'broker': ['docker0:6379'],
             'webserver': ['-:8123']},
    prunekeep = 2,
    maxmemory = 0.7,
    dockerfile = 'Dockerfile'
)
_CONFIGS['__help__docker'] = dict(
    name = """name of the docker images""",
    registry = """a list of docker registries

    For example,
    ["localhost:5000", "e.sovetkin"]
    where "localhost:5000" indicates a locally run docker registry,
    and "e.sovetkin" resolves to a dockerhub one.

    The first registry is a special one, as it is used as the default
    to pull images from. Other registries are a backup""",
    mounts = """a list of mounts

    For instance,
    ["/mnt/dir1:/data/dir1","/mnt/dir2","data"]

    where
      - /mnt/dir1 is a local path, and
        /data/dir1 is a path in the docker container
      - /mnt/dir2 will be mounted at /mnt/dir2 inside docker

      - absolute path "data" will be resolved relative to the git root
        directory of the project on host, and /code directory inside
        the container

    Set "." to mount the git root directly. This is useful for
    debugging, without docker image rebuild.""",
    ports = """a dictionary specifying where docker
    should redirect different services.

    <service name>: [<network interface>:<port>]

    '-' network interace indicates all interfaces

    Be careful, as generic network interface may result in conflic
    with specific network interfaces""",
    prunekeep = """number of older images to keep locally""",
    maxmemory = """percentage of memory allowed to use by docker""",
    dockerfile = """path to the Dockerfile"""
)


_CONFIGS['ssh'] = dict(
    hosts = {}
)
_CONFIGS['__help__ssh'] = dict(
    hosts = """a dictionary of ssh host and instructions what to run there

    For example,
    {'host1': {'path': 'app-name',
               'services': ['worker','webserver','flower','broker']},
     'host2': {'path': 'dir2/app-name',
               'services': ['worker']}}

    """
)

def _format_comment(comment, comment_char = '#'):
    if not isinstance(comment, str):
        raise RuntimeError('comment must be a string!')

    return '\n'.join(['{} {}'.format(comment_char, x) for x in comment.split('\n')])


def _update_section(config, section, entries, comments):
    if not isinstance(entries, dict):
        raise RuntimeError('entries must be a dictionary!')

    res = {}
    for k, v in entries.items():
        if k in comments:
            res[_format_comment(comments[k])] = None

        res[k] = json.dumps(v) \
            if isinstance(v, (list, tuple, dict)) else \
               v

    config[section] = res
    return config


def generate_configs(ofn):
    config = ConfigParser(allow_no_value = True)

    for k, v in _CONFIGS.items():
        if _help_re.match(k):
            continue

        ck = '__help__{}'.format(k)
        cv = _CONFIGS[ck] if ck in _CONFIGS else dict()
        config = _update_section(config, k, v, cv)

    with open(ofn, 'w') as f:
        config.write(f)


def _check_datatype(example, value):
    if not isinstance(value, str):
        return value

    for t in (int, float):
        if isinstance(example, t):
            return t(value)

    if isinstance(example, (list, tuple, dict)):
        return json.loads(value)

    return value


def _ensure_datatypes(s, d):
    if s not in _CONFIGS:
        return d

    for k, v in d.items():
        if k not in _CONFIGS[s]:
            continue

        try:
            d[k] = _check_datatype(_CONFIGS[s][k], v)
        except:
            raise RuntimeError("""
        {}->{}->{} cannot convert to a protype:
        {}""".format(s,k,v,_CONFIGS[s][k]))

    return d


def read_configs(ifn):
    config = ConfigParser()
    try:
        config.read(ifn)
    except:
        config = ConfigParser()
        pass

    res = {}
    for k, v in _CONFIGS.items():
        if _help_re.match(k):
            continue

        if k not in config:
            res[k] = v
            continue

        v.update(_ensure_datatypes(k, dict(config[k])))
        res[k] = v


    for s in config.sections():
        if s in res:
            continue

        res[s] = dict(config[k])

    return res


def _configpath_wrt_path(path):
    return os.path.join(path,'data',
                        'configs','cu.conf')


def write_config_cu(dotnew = True):
    path = _configpath_wrt_path(git_root())

    if os.path.exists(path):
        if dotnew:
            path += ".confnew"
        else:
            raise RuntimeError('File exists and dotnew = False! {}'\
                               .format(path))

    os.makedirs(os.path.dirname(path), exist_ok = True)
    generate_configs(path)
    print(f"{path}")


def read_config_wrt_git():
    root = git_root()
    return root, read_configs(_configpath_wrt_path(root))


def _write_pkgdata(ofn, package, resource):
    data = pkgutil.get_data(package, resource)

    os.makedirs(os.path.dirname(ofn), exist_ok = True)
    if os.path.exists(ofn):
        ofn += ".confnew"

    with open(ofn, 'wb') as f:
        f.write(data)
    return ofn


def write_config_templates():
    from cu import CONFIGS

    data = [{'ofn': os.path.join\
             (git_root(), CONFIGS['docker']['dockerfile']),
             'package': 'cu.configs',
             'resource': 'Dockerfile'},
            {'ofn': os.path.join\
             (git_root(), CONFIGS['logging']['logrotate']),
             'package': 'cu.configs',
             'resource': 'logrotate.conf'}]
    for args in data:
        print(_write_pkgdata(**args))
