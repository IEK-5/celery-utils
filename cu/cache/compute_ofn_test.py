

def test_full_fn_name_1():
    from cu.cache.compute_ofn import _full_fn_name
    assert "cu/cache/compute_ofn/_full_fn_name" == \
        _full_fn_name(_full_fn_name)


def test_full_fn_name_2():
    import cu
    assert "cu/cache/compute_ofn/_full_fn_name" == \
        cu.cache.compute_ofn._full_fn_name(cu.cache.compute_ofn._full_fn_name)


def test_full_fn_name_3():
    from .compute_ofn import _full_fn_name
    assert "cu/cache/compute_ofn/_full_fn_name" == \
        _full_fn_name(_full_fn_name)


def test_full_fn_name_4():
    import cu.cache as cache
    assert "cu/cache/compute_ofn/_full_fn_name" == \
        cache.compute_ofn._full_fn_name(cache.compute_ofn._full_fn_name)


def test_full_fn_name_5():
    from cu.cache.compute_ofn import _full_fn_name
    from cu import upload
    assert "cu/webserver/upload/upload" == \
        _full_fn_name(upload)


def test_full_fn_name_6():
    from cu.cache.compute_ofn import _full_fn_name
    from cu.cache.tasks import call_fn_cache
    assert "celery/local/call_fn_cache" == \
        _full_fn_name(call_fn_cache)
