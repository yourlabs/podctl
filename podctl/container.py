from .build import Build
from .exceptions import WrongResult
from .proc import output
from .visitable import Visitable


class Container(Visitable):
    default_scripts = dict(
        build=Build(),
    )

    @property
    def container_name(self):
        return '-'.join([self.pod.name, self.name])

    @property
    def image_name(self):
        return self.pod.visitor(self.name).variable('repotags')[0]

    async def down(self, script):
        try:
            await script.exec('podman', 'inspect', self.container_name)
        except WrongResult:
            pass
        else:
            try:
                from podctl.console_script import console_script
                argv = console_script.parser.nonoptions
            except AttributeError:
                argv = []
            argv = argv + [self.container_name]
            await script.exec('podman', 'rm', '-f', *argv)

    async def run(self, script):
        await script.exec(
            'podman', 'run',
            '--name', self.container_name,
            ':'.join((self.variable('repo'), self.variable('tags')[0])),
        )

    async def up(self, script):
        try:
            await script.exec('podman', 'inspect', self.container_name)
        except WrongResult as ee:
            output('Container creating', self.name)
            await script.exec(
                'podman', 'run', '-d', '--name', self.container_name,
                self.image_name,
            )
            output('Container created', self.name)
        else:
            output('Container starting', self.name)
            await script.exec('podman', 'start', self.container_name)
            output('Container started', self.name)
