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


import re
import bottle
import logging

from cu.app \
    import CONFIGS

logging.basicConfig(**CONFIGS['webserver_logs_kwargs'])

from cu.utils.calldocs \
    import calldocs

from cu.utils.import_function \
    import import_function

from cu.webserver.utils \
    import format_help

from cu.webserver.utils \
    import format_help, return_exception, \
    call_method, parse_args, serve

from cu.webserver.upload \
    import upload_request_data


_webserver_args = {
    'serve_type': \
    ('file',
     """what webserver outputs

     options:
         - 'file': binary data

         - 'path': {"storage_fn": <remote storage path>}

         - 'deserialise': {"results": <deserialised data>}

           if remote storage path serialised data, then the webserver
           will attempt to deserialise it and sends it back. Note,
           only json-serialisable data can be sent over the
           webserver.""")}


def _check_allowed(method):
    if not isinstance(CONFIGS['app']['allowed_imports'], list):
        raise RuntimeError\
            ("CONFIGS['app']['allowed_imports'] should be a list!")

    for x in CONFIGS['app']['allowed_imports']:
        if re.match(x, method):
            return True
    return False


def _method2module(method):
    method = method.replace('/','.')
    if not _check_allowed(method):
        raise RuntimeError\
            ('{} does match to the allowed imports!'\
             .format(method))

    return import_function(method)


def _process_request_files(request_files):
    res = {}
    for fn in request_files.keys():
        res[fn] = upload_request_data(request_files[fn])
    return res


@bottle.error(404)
def error404(error):
    return {'results': str(error)}


@bottle.route('/api/help/<method:path>', method=['GET','POST'])
def get_help(method):
    try:
        res = calldocs(_method2module(method))
        res['args'].update(_webserver_args)
    except Exception as e:
        return return_exception(e)

    return {'results': format_help(res)}


@bottle.route('/api/<method_str:path>', method=['GET','POST'])
def do_method(method_str):
    args = {}

    if bottle.request.query:
        args.update(bottle.request.query)
    if bottle.request.json:
        args.update(bottle.request.json)
    if bottle.request.params:
        args.update(bottle.request.params)
    if bottle.request.files:
        args.update(_process_request_files(bottle.request.files))

    try:
        method = _method2module(method_str)
        defaults = calldocs(method)['args']
        defaults.update(_webserver_args)
        args = parse_args(data = args, defaults = defaults)
    except Exception as e:
        return return_exception(e)

    webserver_args = {}
    for k in _webserver_args.keys():
        webserver_args[k] = args[k]
        del args[k]

    return serve(call_method(method=method_str, args=args),
                 **webserver_args)


bottle.run(host=CONFIGS['webserver']['host'],
           port=CONFIGS['webserver']['port'],
           server='gunicorn',
           workers=CONFIGS['webserver']['workers'],
           max_requests=CONFIGS['webserver']['max_requests'],
           timeout=CONFIGS['webserver']['timeout'])
