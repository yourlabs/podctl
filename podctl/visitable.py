import asyncio
from copy import copy, deepcopy


class Visitable:
    default_scripts = dict()

    def __init__(self, *visitors, **scripts):
        self.visitors = list(visitors)
        self.scripts = deepcopy(self.default_scripts)
        self.scripts.update(scripts)

        '''
    def script(self, name):
        script = copy(self.scripts[name])
        return script
'''

    def visitor(self, name):
        for visitor in self.visitors:
            if name.lower() == type(visitor).__name__.lower():
                return visitor

    def variable(self, name):
        for visitor in self.visitors:
            if getattr(visitor, name, None) is not None:
                return getattr(visitor, name)
