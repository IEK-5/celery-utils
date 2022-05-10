import os
import time

from celery_utils.decorators \
    import task

from celery_utils.storage.remotestorage_path \
    import RemoteStoragePath, is_remote_path

from celery_utils.utils.files \
    import move_file

from celery_utils.exceptions \
    import NOT_IN_STORAGE


@task(cache = None, get_args_locally = False,
      autoretry_for = [NOT_IN_STORAGE])
def call_fn_cache(result, ofn, storage_type):
    if result is None:
        return ofn

    ofn = RemoteStoragePath\
        (ofn, remotetype = storage_type)
    result_rmt = RemoteStoragePath\
        (result, remotetype = storage_type)

    if os.path.exists(result_rmt.path):
        move_file(result_rmt.path, ofn.path, True)

    if is_remote_path(result):
        ofn.link(result_rmt.path)
        return str(ofn)

    ofn.upload()
    return str(ofn)
