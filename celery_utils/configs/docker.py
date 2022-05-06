import os
import pkgutil

from celery_utils.app \
    import CONFIGS

from celery_utils.utils.git \
    import git_root


def _write_template(ofn):
    data = pkgutil.get_data('celery_utils.configs',
                            'Dockerfile')
    with open(ofn, 'wb') as f:
        f.write(data)


def write_dockerfile(dotnew = True):
    path = os.path.join(git_root(),
                        CONFIGS['docker']['dockerfile'])

    if os.path.exists(path):
        if dotnew:
            path += ".confnew"
        else:
            raise RuntimeError('File exists and dotnew = False! {}'\
                               .format(path))

    os.makedirs(os.path.dirname(path), exist_ok = True)
    _write_template(ofn = path)
    print(f"{path}")
