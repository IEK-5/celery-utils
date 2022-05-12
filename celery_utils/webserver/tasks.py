import logging

from celery_utils.decorators \
    import task

from celery_utils.utils.import_function \
    import import_function

from celery_utils.exceptions \
    import RETRY_GENERATE_TASK_QUEUE


@task(cache = None, debug_info = True,
      autoretry_for = [RETRY_GENERATE_TASK_QUEUE])
def generate_task_queue(call_string, args):
    """Generate processing queue and start the task

    :call_string: a full path to a function that generates a task queue

    :return: the task id of self (prefixed with a string) or raise an
exception on error

    """
    call = import_function(call_string.replace('/','.'))

    if not hasattr(call, 'cu_attr'):
        logging.warning(f"@call is not applied to {call_string}")
        call_retry = tuple()
    else:
        call_retry = tuple(call.cu_attr['autoretry_for'])

    try:
        job = call(**args)
    except call_retry as e:
        raise RETRY_GENERATE_TASK_QUEUE("{}".format(e)) from e

    return job.delay().task_id
