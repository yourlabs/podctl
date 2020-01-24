'''
docker & docker-compose frustrated me, podctl unfrustrates me.
'''

import asyncio
import cli2
import os
import subprocess
import sys
import textwrap

from .pod import Pod


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
    for name, container in console_script.pod.items():
        if not container.base:
            continue

        script = f'.podctl_build_{name}.sh'
        with open(script, 'w+') as f:
            f.write(str(container.script_build()))

        loop = asyncio.events.get_event_loop()
        protocol_factory = lambda: BuildStreamProtocol(
            container=container,
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

    for proc in procs:
        await proc.communicate()


@cli2.option('debug', help='Print debug output', color=cli2.GREEN, alias='d')
async def up(service=None, **kwargs):
    procs = []
    for name, service in console_script.pod.services.items():
        if 'base' not in service:
            continue

        script = f'.podctl_up_{name}.sh'
        with open(script, 'w+') as f:
            f.write(str(service.build()))

        loop = asyncio.events.get_event_loop()
        protocol_factory = lambda: BuildStreamProtocol(
            service=service,
            limit=asyncio.streams._DEFAULT_LIMIT,
            loop=loop,
        )
        transport, protocol = await loop.subprocess_shell(
            protocol_factory,
            f'bash -eux {script}',
        )
        procs.append(asyncio.subprocess.Process(
            transport,
            protocol,
            loop,
        ))

    for proc in procs:
        await proc.communicate()


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
            with open(self.path) as f:
                self.pod = Pod.factory(self.path)
        return super().call(command)


console_script = ConsoleScript(__doc__).add_module('podctl.console_script')
