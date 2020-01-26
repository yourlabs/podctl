'''
docker & docker-compose frustrated me, podctl unfrustrates me.
'''

import asyncio
import cli2
import importlib
import os
import sys

from .container import Container
from .pod import Pod
from .service import Service


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


@cli2.option('debug', help='Print debug output', color=cli2.GREEN, alias='d')
async def build(service=None, **kwargs):
    procs = []
    for name, service in console_script.pod.services.items():
        container = service.container
        if not container.variable('base'):
            continue

        script = f'.podctl_build_{name}.sh'
        with open(script, 'w+') as f:
            f.write(str(container.script('build')))

        loop = asyncio.events.get_event_loop()

        def protocol_factory():
            return BuildStreamProtocol(
                service,
                limit=asyncio.streams._DEFAULT_LIMIT,
                loop=loop,
            )
        transport, protocol = await loop.subprocess_shell(
            protocol_factory,
            f'buildah unshare bash -eux {script}',
        )
        procs.append(asyncio.subprocess.Process(
            transport,
            protocol,
            loop,
        ))

    codes = []
    for proc in procs:
        await proc.communicate()
        codes.append(proc.returncode)

    for code in codes:
        if code != 0:
            return code


class ConsoleScript(cli2.ConsoleScript):
    def __setitem__(self, name, cb):
        if name != 'help':
            cli2.option(
                'file',
                alias='f',
                help='Path to pod definition (default: pod.py)',
                color=cli2.YELLOW,
                default='pod.py',
            )(cb.target)
            cli2.option(
                'home',
                alias='h',
                help=f'Pod home (default is cwd: {os.getcwd()})',
                color=cli2.YELLOW,
                default=os.getcwd(),
            )(cb.target)
        super().__setitem__(name, cb)

    def call(self, command):
        if command.name != 'help':
            self.path = self.parser.options['file']
            self.home = self.parser.options['home']
            self.containers = dict()
            self.pods = dict()
            self.pod = None
            spec = importlib.util.spec_from_file_location('pod', self.path)
            pod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(pod)
            for name, value in pod.__dict__.items():
                if isinstance(value, Container):
                    self.containers[name] = value
                elif isinstance(value, Pod):
                    self.pods[name] = value

            if 'pod' in self.pods:
                self.pod = self.pods['pod']
            if not self.pod:
                self.pod = Pod(*[
                    Service(name, value, restart='no')
                    for name, value in self.containers.items()
                ])
        return super().call(command)


console_script = ConsoleScript(__doc__).add_module('podctl.console_script')
