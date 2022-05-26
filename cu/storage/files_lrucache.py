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
import logging
import diskcache


def _fn2ino(fn):
    """Read as 'filename to inode'

    Used as keys for the part of the dictionary that maps filenames to
    the inode.

    """
    return "fn2ino://{}".format(fn)


def _c_ino(ino):
    """Read as 'count inodes'

    Used as keys for the part of the dictionary that files with the
    give inode.

    """
    return "c_ino://{}".format(ino)


def _s_ino(ino):
    """Read as 'size of inode'

    Used as keys for keeping track of sizes of inodes.

    """
    return "s_ino://{}".format(ino)


class Files_LRUCache:


    def __init__(self, maxsize, path = '.', check_every = 6):
        """Implements LRU list of file paths

        :maxsize: maximum size in GB of stored files

        :path: path where to store diskcache db

        :check_every: number of hours to check the content of cache

        """
        self.maxsize = maxsize*(1024**3)
        self.check_every = check_every * (60**2)

        self.path = path
        os.makedirs(self.path, exist_ok = True)

        path = os.path.join(self.path,"_Files_LRUCache")
        self._deque = diskcache.Deque\
            (directory = path + '_deque')
        self._cache = diskcache.Cache\
            (directory = path + '_cache',
             size_limit = (1024**3))

        self._lock = diskcache.RLock(self._cache, '_lock')

        with self._lock:
            if 'total' not in self._cache:
                self._cache['total'] = 0
            if 'checked_at' not in self._cache:
                self._cache['checked_at'] = time.time()


    def _inc_c_ino(self, ino):
        c = _c_ino(ino)

        if c not in self._cache:
            self._cache[c] = 1
            return True

        self._cache[c] += 1
        return self._cache[c] == 1


    def _dec_c_ino(self, ino):
        c = _c_ino(ino)

        if c not in self._cache:
            return False

        self._cache[c] -= 1

        if self._cache[c] < 0:
            logging.warning("something is fishy! self._cache[c] < 0")
            self._cache[c] = 0

        if 0 == self._cache[c]:
            del self._cache[c]
            return True

        return False


    def _add_size(self, ino, size):
        s = _s_ino(ino)

        if s in self._cache and size == self._cache[s]:
            return

        self._cache['total'] += size

        if s not in self._cache:
            self._cache[s] = size
            return

        if size != self._cache[s]:
            self._cache['total'] -= self._cache[s]
            self._cache[s] = size


    def _remove_size(self, ino):
        s = _s_ino(ino)

        if s not in self._cache:
            return False

        self._cache['total'] -= self._cache[s]
        del self._cache[s]
        return True


    def _remove_fn(self, fn):
        f = _fn2ino(fn)

        if f not in self._cache:
            return False

        if self._dec_c_ino(self._cache[f]):
            self._remove_size(self._cache[f])
        del self._cache[f]

        return True


    def _add_fn(self, fn):
        f = _fn2ino(fn)

        if not os.path.exists(fn):
            # case, when file does not exist/disappeared
            if self._remove_fn(fn):
                self._deque.remove(fn)
            return

        ino = os.stat(fn).st_ino
        size = os.stat(fn).st_size

        # case when fn is seen the first time
        if f not in self._cache:
            self._inc_c_ino(ino)

        # the case, when inode of filename has been changed
        if f in self._cache and self._cache[f] != ino:
            self._inc_c_ino(ino)
            if self._dec_c_ino(self._cache[f]):
                self._remove_size(self._cache[f])

        # this updates the size of the ino
        self._add_size(ino, size)
        self._cache[f] = ino


    def check_content(self):
        """Check content of lists and remove deleted files
        """
        with self._lock:
            [self._add_fn(p) for p in self._deque]


    def _update_order(self, fn):
        if fn in self._deque:
            self._deque.remove(fn)
        self._deque.append(fn)



    def _update(self, fn):
        self._update_order(fn)
        self._add_fn(fn)

        if (time.time() - self._cache['checked_at']) > self.check_every:
            self._cache['checked_at'] = time.time()
            self.check_content()


    def add(self, fn):
        """Add a file to a cache

        File does not have to exist at a time of addition. Any query
        about the file updates information in cache.

        :fn: path to a file

        """
        with self._lock:
            while self._cache['total'] >= self.maxsize \
                  and len(self._deque) > 0:
                self.popleft()
            self._update(fn)


    def __contains__(self, fn):
        if fn not in self._deque:
            return False

        with self._lock:
            self._update(fn)

        if not os.path.exists(fn):
            return False

        return True


    def __len__(self):
        return len(self._deque)


    def size(self):
        """Return total used space in bytes
        """
        return self._cache['total']


    def popleft(self):
        """Pop the least recently used file

        Popping tries to delete the tracked by cache file.
        """
        with self._lock:
            fn = self._deque.popleft()
            try:
                os.remove(fn)
            except:
                pass

            self._remove_fn(fn)
            logging.debug("""
            file is removed from cache: {}
            Files_LRUCache size: {:.5f} GB
            Files_LRUCache usage: {:.2%}
            """.format(fn, self.size()/(1024**3),
                       self.size() / self.maxsize))
            return fn
