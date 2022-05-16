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


from functools import wraps

from cu.storage.remotestorage_path \
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
