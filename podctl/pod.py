import asyncio
import copy
import os

from .build import Build
from .container import Container
from .exceptions import WrongResult
from .script import Script
from .visitable import Visitable


class Up(Script):
    async def run(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        pod = kwargs.get('pod')

        try:
            pod.info = (await self.exec(
                'podman', 'pod', 'inspect', pod.name
            )).json
            print(f'Pod {pod.name} ready')
        except WrongResult:
            print(f'Pod {pod.name} creating')
            await self.exec(
                'podman', 'pod', 'create', '--name', self.pod.name,
            )
            print(f'Pod {pod.name} created')
            pod.info = (await self.exec(
                'podman', 'pod', 'inspect', pod.name
            )).json

        return await super().run(*args, **kwargs)


class Pod(Visitable):
    default_scripts = dict(
        build=Build(),
        run=Script('run', 'Run a container command'),
        up=Up('up', 'Start the stack'),
        test=Script('test', 'Run tests inside containers'),
    )

    @property
    def name(self):
        return os.getenv('POD', os.getcwd().split('/')[-1])

    @property
    def containers(self):
        return [i for i in self.visitors if type(i) == Container]

    def script(self, name):
        async def cb(*args, **kwargs):
            asyncio.events.get_event_loop()
            script = copy.deepcopy(self.scripts[name])
            kwargs['pod'] = self
            return await script.run(*args, **kwargs)
        return cb
