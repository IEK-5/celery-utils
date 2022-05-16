# Tools to make distributed services with celery

The `cu` provides a way to create distributed services. We use the [celery](https://github.com/celery/celery) queue management system, hence the name of our tool.

`cu` package turns any python code into a distributed web service. It allows organising functions into a tree of tasks, where task results are cached in shared storage.

[Wiki](https://github.com/esovetkin/celery-utils/wiki) pages contain detailed documentation and examples.

**!!! this package is still in development !!! todos:**

  - restrict resources for different instances of specific per node

    this needs a special service

    I might get away without this, as multiple services can be packed
    together in a single cu thing.

    However, if software needs really different containers, then such
    service can come handy.

    Perhaps, such orchestration can be done passively via redis, but I
    don't know how to influence the celery task allocation at runtime.

  - handling of logs

    beat task that collect / rotate logs or on demand

    it cannot happen only, perhaps only on service restart or so

  - storage purging:

    now tasks inherit attributes, that contain enough information to purge files periodically

    ? how to ensure that some bug will not purge something important ?

    ? storage purging is for arbitrary remote storages

    purging functions should operate with generators that generate
    file paths

  - docs and arguments passing

    webserver has serve_type for example, how to handle this?

  - autossh mount

    service to automount ssh directories

  - check on cu level, that -s are sensible. Otherwise one just gets
    some errors in docker.

  - make call cache work for pickle stuff

  - change "latest" to "stable" and "dev" for docker images

    add corresponding flags for "stable" and "dev" (development)
    versions of the docker images

  - set docker image names via config

    the --app is too obscure

  - run docker as specific user

  - how to organise multiple projects/app to share

  - how to do tests?

  - ssh remote host should have celery_utils installed, as one needs to do cu_restart

  - upload and download API for webserver
