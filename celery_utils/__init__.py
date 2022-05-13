from celery_utils.decorators import call
from celery_utils.decorators import task

from celery_utils.exceptions import TASK_RUNNING, NOT_IN_STORAGE
from celery_utils.app import CELERY_APP
from celery_utils.app import CONFIGS

CELERY_APP.autodiscover_tasks(CONFIGS['app']['autodiscover'])
