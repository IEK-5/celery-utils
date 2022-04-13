from celery_utils.decorators.jobs \
    import task_decorator

from celery_utils.utils.import_function \
    import import_function


@task_decorator(cache = None,
                debug_info = True)
def generate_task_queue(call_string, args):
    """Generate processing queue and start the task

    :call_string: a full path to a function that generates a task queue

    :return: the task id of self (prefixed with a string) or raise an
exception on error

    """
    call = import_function(call_string.replace('/','.'))
    job = call(**args).delay() # call(**args) takes time
    return job.task_id
