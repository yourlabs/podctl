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
        for name, script in self.podfile.pod.scripts.items():
            cb = self.podfile.pod.script(name)
            cb.__doc__ = inspect.getdoc(script)
            self[name] = cli2.Callable(name, cb)
        return super().__call__(*args, **kwargs)

    def call(self, command):
        try:
            return super().call(command)
        except Mistake as e:
            print(e)
            sys.exit(1)
        except WrongResult:
            sys.exit(1)


console_script = ConsoleScript(__doc__).add_module('podctl.console_script')
