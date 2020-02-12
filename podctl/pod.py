import asyncio
import copy
import os

from .build import Build
from .container import Container
from .run import Run
from .script import Script
from .visitable import Visitable


class Pod(Visitable):
    default_scripts = dict(
        build=Build(),
        run=Run(),
    )

    @property
    def containers(self):
        return [i for i in self.visitors if type(i) == Container]

    def script(self, name):
        async def cb(*args, **kwargs):
            asyncio.events.get_event_loop()
            script = copy.deepcopy(self.scripts[name])

            if args:
                containers = [c for c in self.containers if c.name in args]
            else:
                containers = self.containers

            procs = []
            for container in containers:
                procs.append(script(
                    container,
                    *args,
                    container=container,
                    pod=self,
                    **kwargs,
                ))
            return await asyncio.gather(*procs)
        return cb
