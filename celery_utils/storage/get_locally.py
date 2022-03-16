from functools import wraps

from celery_utils.storage.remotestorage_path \
    import RemoteStoragePath, is_remote_path


def _get_locally_item(x):
    if isinstance(x, dict):
        x = {k:_get_locally_item(v) for k,v in x.items()}

    if isinstance(x, (list, tuple)) and \
       len(x) and isinstance(x[0], str):
        x = [_get_locally_item(v) for v in x]

    if isinstance(x, str) and is_remote_path(x):
        x = RemoteStoragePath(x).get_locally()

    return x


def _get_locally(*args, **kwargs):
    """Make sure all remote files are available locally

    Note, only the first level of argument is walked. For example, if
    argument is a list of files, this list is not checked.
    """
    args = [_get_locally_item(x) for x in args]

    kwargs = {k:_get_locally_item(v) \
              for k,v in kwargs.items()}

    return args, kwargs


def get_locally(fun):
    """Get locally all remove storage items
    """
    @wraps(fun)
    def wrapper(*args, **kwargs):
        args, kwargs = _get_locally(*args, **kwargs)
        return fun(*args, **kwargs)
    return wrapper
