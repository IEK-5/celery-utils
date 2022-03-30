from importlib import import_module


def import_function(path):
    try:
        mname, fname = path.rsplit('.', 1)
    except ValueError as e:
        raise ModuleNotFoundError('invalid path = {}'.format(path)) from e

    module = import_module(mname)

    return getattr(module, fname)
