'''
docker & docker-compose frustrated me, podctl unfrustrates me.
'''

import asyncio
import cli2
import inspect
import os
import sys

from .container import Container
from .pod import Pod
from .exceptions import Mistake, WrongResult
from .service import Service


class ConsoleScript(cli2.ConsoleScript):
    def __call__(self, *args, **kwargs):
        import inspect
        from podctl.podfile import Podfile
        self.podfile = Podfile.factory(os.getenv('PODFILE', 'pod.py'))
        for name in self.podfile.pod.script_names():
            self[name] = self.podfile.pod.script(name)
            '''
            ee = self.script(pod, name)
            ee.__doc__ = inspect.getdoc(cb)
            self[name] = cli2.Callable(name, ee)
            '''

        super().__call__(*args, **kwargs)

    @staticmethod
    def script(script_name):
        async def script(*services_or_flags, **options):
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
                procs.append(service.container.script(script_name, flags))

            try:
                result = await asyncio.gather(*procs)
            except Mistake as e:
                print(e)
                sys.exit(1)
            except WrongResult:
                sys.exit(1)
        return script


console_script = ConsoleScript(__doc__).add_module('podctl.console_script')
