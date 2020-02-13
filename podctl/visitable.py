import asyncio
from copy import copy, deepcopy


class Visitable:
    default_scripts = dict()

    def __init__(self, *visitors, **scripts):
        self.visitors = list(visitors)
        self.scripts = deepcopy(self.default_scripts)
        self.scripts.update(scripts)

    def visitor(self, name):
        for visitor in self.visitors:
            if name.lower() in (
                type(visitor).__name__.lower(),
                getattr(visitor, 'name', '')
            ):
                return visitor

    def variable(self, name):
        for visitor in self.visitors:
            if getattr(visitor, name, None) is not None:
                return getattr(visitor, name)
