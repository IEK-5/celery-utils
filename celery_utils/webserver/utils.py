import re
import json
import celery
import inspect
import traceback

from celery.result \
    import AsyncResult

from celery_utils.storage.remotestorage_path \
    import searchandget_locally, is_remote_path

from celery_utils.exceptions \
    import TASK_RUNNING

from celery_utils.app \
    import get_Tasks_Queues, CONFIGS

from celery_utils.webserver.tasks \
    import generate_task_queue


def return_exception(e):
    return {'results':
            {'error': type(e).__name__ + ": " + str(e),
             'traceback': traceback.format_exc()}}


def parse_args(data, defaults):
    res = {}

    if not data:
        data = {}
    if not defaults:
        return res

    for key, _ in data.items():
        if key not in defaults:
            raise RuntimeError("Unknown argument: '%s'" % key)

    for key, (item, _) in defaults.items():
        if key not in data:
            if item is inspect._empty:
                raise RuntimeError\
                    ("{} is missing and a required argument")
            res[key] = item
            continue

        new = data[key]
        if type(item) != type(new) \
           and isinstance(new, str) \
           and isinstance(item, (list, dict)):
            new = json.loads(new)
        res[key] = type(item)(new)

    return res


def format_help(data):
    res = []
    res += ["{}\n".format(data['header'])]

    for k, v in data['args'].items():
        if not isinstance(v, tuple) or 2 != len(v):
            raise RuntimeError\
                ('value of the help dictionary must be '
                 'a tuple of length 2! Got instead: {}'\
                 .format(v))

        default, docs = v
        if default is inspect._empty:
            default = '<no default>, a required argument'

        res += [("""
        {} = {}
            {}

        """.format(k, default, docs)).lstrip()]

    return '\n'.join(res)


def serve(data, serve_type = 'file'):
    if isinstance(data, dict):
        return data

    if is_remote_path(data):
        if 'file' == serve_type:
            with open(searchandget_locally(data),'rb') as f:
                return f.read()
        elif 'path' == serve_type:
            return {'storage_fn': data}
        else:
            raise RuntimeError('unknow serve_type = {}'\
                               .format(serve_type))

    return {'results': data}


def _cleanup_job(job, key = None):
    job.forget()
    if key:
        tasks_queues = get_Tasks_Queues()
        del tasks_queues[key]


def get_job_results(job_id, key, timeout):
    job = AsyncResult(job_id)

    try:
        state = job.state
        if 'SUCCESS' == state:
            fn = job.result
        elif 'PENDING' == state \
             or 'STARTED' == state \
             or 'RETRY' == state:
            fn = job.wait(timeout = timeout)
        elif 'FAILURE' == state:
            res = job.result
            if not isinstance(res, BaseException):
                raise RuntimeError\
                    ("""FAILURE state is not an exception!..
                    job.result = {}""".format(res))
            raise res
        elif 'REVOKED' == state:
            raise RuntimeError\
                ("""job_id = {} is REVOKED!"""\
                 .format(job_id))
        else:
            return {'results': {'message': 'task is running',
                                'state': state}}
    except TASK_RUNNING:
        return {'results': {'message': 'task is running'}}
    except celery.exceptions.TimeoutError:
        return {'results': {'message': 'task is running'}}
    except Exception as e:
        _cleanup_job(job, key)
        return return_exception(e)

    # this line is not reached in case TASK_RUNNING
    _cleanup_job(job, key)

    return fn


def _method_results(method, args):
    tasks_queues = get_Tasks_Queues()
    job_id = tasks_queues[(method, args)]

    # determine if task is generate_task_queue type
    m = re.match('generate_task_queue://(.*)', job_id)
    if m:
        job_id = get_job_results\
            (m.groups()[0],
             timeout = \
             int(CONFIGS['webserver']['timeout']),
             key = (method, args))

    if isinstance(job_id, dict):
        return job_id

    tasks_queues[(method, args)] = job_id

    return get_job_results\
        (job_id,
         timeout = \
         int(CONFIGS['webserver']['timeout']),
         key = (method, args))


def call_method(method, args):
    tasks_queues = get_Tasks_Queues()

    if (method, args) in tasks_queues:
        return _method_results(method, args)

    try:
        job = generate_task_queue.delay(method, args)
        tasks_queues[(method, args)] = \
            "generate_task_queue://{}".format(job.task_id)
    except Exception as e:
        return return_exception(e)

    return _method_results(method, args)
