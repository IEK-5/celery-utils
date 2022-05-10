import pytest

from celery_utils.utils.matchargs \
    import matchargs


def _fun1(a,b,c):
    return '{},{},{}'.format(a,b,c)


def _fun2(a, **kwargs):
    return '{},{}'.format(a,kwargs)


def _fun3(*args):
    return args


def _fun4(a='a',b='b'):
    return '{},{}'.format(a,b)


def test_matchargs_fun1():
    assert 'a,b,c' == matchargs(_fun1)(a='a',b='b',c='c')
    assert 'a,b,c' == matchargs(_fun1)(a='a',b='b',c='c',d='d')
    assert 'a,b,c' == matchargs(_fun1)(a='a',**{'b':'b','c':'c'})

    with pytest.raises(TypeError):
        matchargs(_fun1)(d='d')

    with pytest.raises(RuntimeError):
        matchargs(_fun1)('a','b','c')


def test_matchargs_fun2():
    matchargs(_fun2)(a='a', b='b', c='c')
    matchargs(_fun2)(a='a', **{'b':'b','c':'c'})


def test_matchargs_fun3():
    with pytest.raises(RuntimeError):
        assert matchargs(_fun3)()


def test_matchargs_fun4():
    assert 'a,b' == matchargs(_fun4)()
    assert 'a,b' == matchargs(_fun4)(a='a')
    assert 'a,b' == matchargs(_fun4)(b='b')
