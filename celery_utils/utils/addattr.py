class AddAttr(object):
    """Add additional attributes to the celery.Task class

    """

    def __init__(self, **kwargs):
        self._kwargs = kwargs


    def __call__(self, cls):
        class Wrapped(cls):
            cu_attr = self._kwargs

        return Wrapped
