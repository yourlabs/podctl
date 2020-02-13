import os

from .build import Build
from .container import Container
from .scripts import *
from .visitable import Visitable


class Pod(Visitable):
    default_scripts = dict(
        build=Build(),
        up=Up('up', 'Start the stack'),
        down=Down('down', 'Destroy the stack'),
        run=Run('run', 'Run a command in container(s)'),
        name=Name(
            'name',
            'Output the pod name for usage with podman',
        ),
    )

    def script(self, name):
        async def cb(*args, **kwargs):
            asyncio.events.get_event_loop()
            kwargs['pod'] = self
            return await self.scripts[name].run(*args, **kwargs)
        return cb

    async def down(self, script):
        try:
            await script.exec('podman', 'pod', 'inspect', self.name)
        except WrongResult:
            pass
        else:
            await script.exec('podman', 'pod', 'rm', self.name)

    async def up(self, script):
        try:
            await script.exec(
                'podman', 'pod', 'inspect', self.name
            )
            print(f'{self.name} | Pod ready')
        except WrongResult:
            print(f'{self.name} | Pod creating')
            await script.exec(
                'podman', 'pod', 'create', '--name', self.name,
            )
            print(f'{self.name} | Pod created')

    @property
    def name(self):
        return os.getenv('POD', os.getcwd().split('/')[-1])

    @property
    def containers(self):
        return [i for i in self.visitors if type(i) == Container]

    def __repr__(self):
        return self.name
