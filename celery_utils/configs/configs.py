import os
import re
import json

from configparser \
    import ConfigParser

from json.decoder \
    import JSONDecodeError

from celery_utils.utils.git \
    import git_root


_help_re = re.compile(r'__help__.*')

# _CONFIGS are used to generate default config file
_CONFIGS = dict()

_CONFIGS['app'] = dict(
    allowed_imports = ['celery_utils.*'])
_CONFIGS['__help__app'] = dict(
    allowed_imports = """
List of strings with regex that should be match for allowed modules to
be called from the webserver """)

_CONFIGS['redis'] = dict(
    url = 'localhost',
    port = 6379,
    db = 0,
    result_expires = 7200)
_CONFIGS['__help__redis'] = dict(
    url = 'address of the redis broker service',
    port = 'port of the redis broker',
    db = 'which db to use. should be a number between 0 and 15',
    result_expires = 'expiration time (in seconds) for stored task results')

_CONFIGS['worker'] = dict(
    workers = 2,
    max_memory = 2097152)
_CONFIGS['__help__worker'] = dict(
    workers = 'maximum number of workers on node',
    max_memory = """
Maximum amount of resident memory (in KiB),
that may be consumed by a child process
before it will be replaced by a new one""")

_CONFIGS['localcache'] = dict(
    path = 'data/results_cache',
    limit = 10)
_CONFIGS['__help__localcache'] = dict(
    path = 'path where local data is stored',
    limit = 'maximum size of local cache in GB')

_CONFIGS['remotestorage'] = dict(
    use_remotes = ["localmount_"],
    default = 'localmount_dir')
_CONFIGS['__help__remotestorage'] = dict(
    use_remotes = """
Specify which remotes storage to use

  'localmount_' indicates a local directory.
  For that a configuration section should exists
  that contains directory locations.""",
    default = 'Default remote storage to use')

_CONFIGS['localmount_'] = dict(
    dir = '/data/dir')
_CONFIGS['__help__localmount_'] = dict(
    dir = """
Path for 'localmount_dir' remote storage.""")

_CONFIGS['webserver'] = dict(
    host = '0.0.0.0',
    port = 8123,
    workers = 2,
    max_requests = 100,
    timeout = 20)
_CONFIGS['__help__webserver'] = dict(
    host = """
IP address for a webserver to listen requests to
""",
    port = """
Port for a webserver to listen requests to
""",
    workers = """
Number of workers for a webserver
""",
    max_requests = """
Maximum number of requests before webserver gives up
""",
    timeout = """
Timeout for a webserver request
""")

_CONFIGS['logging'] = dict(
    path = 'data/logs',
    level = 'INFO')
_CONFIGS['__help__logging'] = dict(
    path = 'path for storing logs',
    level = 'level of log messages')

_CONFIGS['flower'] = dict(
    port = 5555)
_CONFIGS['__help__flower'] = dict(
    port = 'port to use for the flower service')


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
                        'configs','celery_utils.conf')


def write_config_wrt_git(dotnew = True):
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
