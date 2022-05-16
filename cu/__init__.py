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

from cu.app import CELERY_APP
from cu.app import CONFIGS

from cu.cache.cache import cache

from cu.decorators import call
from cu.decorators import task

from cu.exceptions import TASK_RUNNING, NOT_IN_STORAGE

from cu.webserver.upload import upload, download

CELERY_APP.autodiscover_tasks(CONFIGS['app']['autodiscover'])
