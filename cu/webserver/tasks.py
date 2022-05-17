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


import logging

from cu.decorators \
    import task

from cu.utils.import_function \
    import import_function

from cu.exceptions \
    import RETRY_GENERATE_TASK_QUEUE


@task(cache = False, get_args_locally = False,
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
        return job.delay().task_id
    except call_retry as e:
        raise RETRY_GENERATE_TASK_QUEUE("{}".format(e)) from e

