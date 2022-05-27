from .calldocs import calldocs


def g(d):
     """Description of g

     :d: first argument

     second line

     third line

     :return: return
     """
     return c


def f(a,b,c):
     """Description

     Longer line. Bla-bla

     :a: first argument

     second line

     :b,c: second and third arguments
     third line

     :return: return
     """
     return a+b


def h(a,b):
    """
    :a: a
    :b: b
    :return: return
    """


def cl(string):
    res = string[1].count('\n')
    if 0 == res:
        res = 1
    return res


def test_parsing():
    docs = calldocs(f, calldocs_tail=[g])

    assert 2 == docs['header'].count('\n')
    assert 4 == len(docs['args'].keys())
    assert 2 == cl(docs['args']['a'])
    assert 1 == cl(docs['args']['b'])
    assert 1 == cl(docs['args']['c'])
    assert 4 == cl(docs['args']['d'])


def test_options():
    docs = calldocs(f, calldocs_options={'a': (1,'first'),'b':(2,'second')})

    assert 2 == docs['header'].count('\n')
    assert 3 == len(docs['args'].keys())
    assert 1 == cl(docs['args']['a'])
    assert 1 == cl(docs['args']['b'])
    assert 1 == cl(docs['args']['c'])


def test_empty_header():
    docs = calldocs(h)

    assert 'h' == docs['header']
    assert 1 == cl(docs['args']['a'])
    assert 1 == cl(docs['args']['b'])
