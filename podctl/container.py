import asyncio
import os

from .build import Build
from .visitable import Visitable


class BuildStreamProtocol(asyncio.subprocess.SubprocessStreamProtocol):
    def __init__(self, service, *args, **kwargs):
        self.service = service
        super().__init__(*args, **kwargs)

    def pipe_data_received(self, fd, data):
        if fd in (1, 2):
            for line in data.split(b'\n'):
                if not line:
                    continue
                sys.stdout.buffer.write(
                    self.service.name.encode('utf8') + b' | ' + line + b'\n'
                )
            sys.stdout.flush()
        super().pipe_data_received(fd, data)


def protocol_factory():
    loop = asyncio.events.get_event_loop()
    return BuildStreamProtocol(
        service,
        limit=asyncio.streams._DEFAULT_LIMIT,
        loop=loop,
    )


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

    async def script(self, name, loop):
        self.packages = []
        for visitor in self.visitors:
            self.packages += getattr(visitor, 'packages', [])
        result = await super().script(name, loop)
        return result

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
