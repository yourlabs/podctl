from .build import Build
from .exceptions import WrongResult
from .visitable import Visitable


class Container(Visitable):
    default_scripts = dict(
        build=Build(),
    )

    @property
    def container_name(self):
        return '-'.join([self.pod.name, self.name])

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
            tag = ':'.join((
                self.variable('repo'),
                self.variable('tags')[0],
            ))
            print(f'{self.name} | Container creating')
            await script.exec(
                'podman', 'run', '-d', '--name', self.container_name,
                tag,
            )
            print(f'{self.name} | Container created')
        else:
            print(f'{self.name} | Container starting')
            await script.exec('podman', 'start', self.container_name)
            print(f'{self.name} | Container started')
