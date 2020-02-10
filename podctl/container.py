import asyncio
import os
import shlex

from .build import Build
from .visitable import Visitable


class Container(Visitable):
    default_scripts = dict(
        build=Build,
    )
    paths = [
        '/bin',
        '/sbin',
        '/usr/bin',
        '/usr/sbin',
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log = []

    async def script(self, name, flags, loop=None):
        self.loop = loop or asyncio.events.get_event_loop()
        self.packages = []
        for visitor in self.visitors:
            self.packages += getattr(visitor, 'packages', [])
        result = await super().script(name, loop)
        return result
