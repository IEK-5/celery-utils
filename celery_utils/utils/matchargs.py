import inspect

from functools import wraps


def matchargs(fun):
    """Match list of kwargs to the arguments a function

    :func: a function to call

    :kwargs: key word arguments

    """
    spec = inspect.getfullargspec(fun)

    if spec.varargs:
        raise RuntimeError\
            ("matchargs is not applicable for "
             "functions with positional arguments")

    @wraps(fun)
    def wrapper(*args, **kwargs):
        if len(args):
            raise RuntimeError\
            ("matchargs is not applicable for "
             "functions with positional arguments")

        if spec.varkw:
            return fun(**kwargs)

        return fun(**{k:v \
                      for k,v in kwargs.items() \
                      if k in spec.args})
    return wrapper
