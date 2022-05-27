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


import re
import inspect


class _FunDocs:


    def __init__(self, fun,
                 docs_re = r'\s*:([^:]+):\s*([^:]+)',
                 argsplit = r'[,;]\s*',
                 docs_process = (r'\n\s*',r' ')):
        self._fun = fun
        self._re = re.compile(docs_re)
        self._split = re.compile(argsplit)
        self._doc = (re.compile(docs_process[0]),
                     docs_process[1])


    @property
    def header(self):
        res = []

        docs = inspect.getdoc(self._fun)
        if docs is None:
            return self._fun.__name__

        for line in docs.split('\n\n'):
            if self._re.match(line):
                break
            res += [line]

        if 0 == len(res):
            return self._fun.__name__
        return '\n\n'.join(res)


    @property
    def _docs(self):
        res = {}

        docs = inspect.getdoc(self._fun)
        if docs is None:
            return res

        cur = None
        for line in docs.split('\n\n'):
            if not self._re.match(line):
                if cur is not None:
                    res[cur] += """

            {}""".format(line)
                    continue

            for args, docs in self._re.findall(line):
                docs = self._doc[0].sub(self._doc[1], docs)
                for a in self._split.split(args):
                    res[a] = docs
                    cur = a

        return res


    def __getitem__(self, arg):
        if arg not in self._docs:
            return ''

        return self._docs[arg]


def _compute_calldocs(fun, options):
    res = {}
    docs = _FunDocs(fun)

    for arg, param in inspect.signature(fun).parameters.items():
        if arg in options:
            res[arg] = options[arg]
            continue

        res[arg] = (param.default, docs[arg])

    return {'header': docs.header, 'args':res}


def _deduce_calldocs(fun, options):
    if hasattr(fun, '_calldocs'):
        return getattr(fun, '_calldocs')

    return _compute_calldocs(fun, options)


def calldocs(fun, calldocs_options = {}, calldocs_tail = []):
    res = {'header': '', 'args': {}}

    for f in calldocs_tail[::-1]:
        res['args'].update(_deduce_calldocs(f,{})['args'])

    x = _deduce_calldocs(fun, calldocs_options)
    res['args'].update(x['args'])
    res['header'] = x['header']
    return res
