import os

from .build import Build
from .visitable import Visitable


class Container(Visitable):
    default_scripts = dict(
        build=Build,
    )

    def script(self, name):
        self.packages = []
        for visitor in self.visitors:
            self.packages += getattr(visitor, 'packages', [])
        return super().script(name)

    def script_run(self, name, debug):
        script = f'.podctl_build_{name}.sh'
        with open(script, 'w+') as f:
            f.write(str(self.script('build')))

        if os.getenv('BUILDAH_ISOLATION') == 'chroot':
            prefix = ''
        else:
            prefix = 'buildah unshare '

        x = 'x' if debug else ''
        return prefix + f'bash -eu{x} {script}'

    async def build(self, loop, protocol_factory):
        transport, protocol = await loop.subprocess_shell(
            protocol_factory,
            cmd,
        )
        await asyncio.subprocess.Process(
            transport,
            protocol,
            loop,
        ).communicate()
