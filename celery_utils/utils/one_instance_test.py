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


import time

from celery_utils.utils.tasks \
    import task_test_queueonce


def test_queueonce():
    from celery_utils.exceptions import TASK_RUNNING

    a = task_test_queueonce.delay(sleep = 2, dummy = 1)
    b = task_test_queueonce.delay(sleep = 1, dummy = 1)
    c = task_test_queueonce.delay(sleep = 2, dummy = 1)

    time.sleep(5)
    assert 'FAILURE' == c.state
    assert isinstance(c.result, TASK_RUNNING)
    assert 'SUCCESS' == a.state
    assert a.result
    assert 'SUCCESS' == b.state
    assert b.result
