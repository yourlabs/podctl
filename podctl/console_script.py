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
from .proc import WrongResult
from .service import Service


@cli2.option('debug', help='Print debug output', color=cli2.GREEN, alias='d')
async def build(*services_or_flags, **kwargs):
    flags = []
    services = []
    for arg in services_or_flags:
        if arg.startswith('-') or arg.startswith('+'):
            flags.append(arg)
        else:
            services.append(arg)

    if services:
        services = {
            k: v
            for k, v in console_script.pod.services.items()
            if k in services
        }
    else:
        services = console_script.pod.services

    procs = []
    asyncio.events.get_event_loop()
    for name, service in services.items():
        service.container.name = name
        service.container.flags = flags
        procs.append(service.container.script('build', flags))

    try:
        result = await asyncio.gather(*procs)
    except WrongResult:
        sys.exit(1)


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
