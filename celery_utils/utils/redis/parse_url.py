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


from urllib.parse \
    import urlparse, parse_qsl


def parse_url(url):
    """
    Parse the argument url and return a redis connection.
    Three patterns of url are supported:
        * redis://host:port[/db][?options]
        * redis+socket:///path/to/redis.sock[?options]
        * rediss://host:port[/db][?options]
    A ValueError is raised if the URL is not recognized.

    Taken from: https://github.com/cameronmaske/celery-once/blob/master/celery_once/backends/redis.py

    """
    parsed = urlparse(url)
    kwargs = parse_qsl(parsed.query)

    # TCP redis connection
    if parsed.scheme in ['redis', 'rediss']:
        details = {'host': parsed.hostname}
        if parsed.port:
            details['port'] = parsed.port
        if parsed.password:
            details['password'] = parsed.password
        db = parsed.path.lstrip('/')
        if db and db.isdigit():
            details['db'] = db
        if parsed.scheme == 'rediss':
            details['ssl'] = True

    # Unix socket redis connection
    elif parsed.scheme == 'redis+socket':
        details = {'unix_socket_path': parsed.path}
    else:
        raise ValueError('Unsupported protocol %s' % (parsed.scheme))

    # Add kwargs to the details and convert them to the appropriate type, if needed
    details.update(kwargs)
    if 'socket_timeout' in details:
        details['socket_timeout'] = float(details['socket_timeout'])
    if 'db' in details:
        details['db'] = int(details['db'])

    return details
