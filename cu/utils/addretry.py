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


class AddRetry(object):
    """Add retry options to the celery.Task class

    """

    def __init__(self,
                 autoretry_for = [],
                 max_retries = 10,
                 retry_backoff = True,
                 retry_backoff_max = 600,
                 retry_jitter = True):
        """Make task subclass with specified retry options

        see options in:
        https://docs.celeryproject.org/en/stable/userguide/tasks.html#automatic-retry-for-known-exceptions

        Example:
        CELERY_APP(..., base = AddRetry(...)(celery.Task))

        """
        self.autoretry_for = autoretry_for
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.retry_backoff_max = retry_backoff_max
        self.retry_jitter = retry_jitter


    def __call__(self, cls):
        class Wrapped(cls):
            autoretry_for = self.autoretry_for
            max_retries = self.max_retries
            retry_backoff = self.retry_backoff
            retry_backoff_max = self.retry_backoff_max
            retry_jitter = self.retry_jitter

        return Wrapped
