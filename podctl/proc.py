"""
Asynchronous process execution wrapper.
"""

import asyncio
import shlex
import sys

from .exceptions import WrongResult


class PrefixStreamProtocol(asyncio.subprocess.SubprocessStreamProtocol):
    """
    Internal subprocess stream protocol to add a prefix in front of output to
    make asynchronous output readable.
    """

    def __init__(self, prefix, *args, **kwargs):
        self.prefix = prefix
        super().__init__(*args, **kwargs)

    def pipe_data_received(self, fd, data):
        from .console_script import console_script
        debug = console_script.options.get('debug', False)

        if (debug is True or 'out' in str(debug)) and fd in (1, 2):
            for line in data.split(b'\n'):
                if not line:
                    continue
                sys.stdout.buffer.write(
                    self.prefix.encode('utf8') + b' | ' + line + b'\n'
                    if self.prefix else line + b'\n'
                )
            sys.stdout.flush()
        super().pipe_data_received(fd, data)


def protocol_factory(prefix):
    def _p():
        return PrefixStreamProtocol(
            prefix,
            limit=asyncio.streams._DEFAULT_LIMIT,
            loop=asyncio.events.get_event_loop()
        )
    return _p


class Proc:
    """
    Subprocess wrapper.

    Example usage::

        proc = Proc('find', '/', prefix='containername')

        await proc()     # execute

        print(proc.out)  # stdout
        print(proc.err)  # stderr
        print(proc.rc)   # return code
    """

    def __init__(self, *args, prefix=None, raises=True):
        if len(args) == 1:
            if isinstance(args[0], (list, tuple)):
                args = args[0]
            else:
                args = ['sh', '-euc', ' '.join(args)]
        self.args = [str(a) for a in args]
        self.cmd = shlex.join(self.args)
        self.prefix = prefix
        self.raises = raises
        self.called = False
        self.communicated = False

    async def __call__(self, wait=True):
        if self.called:
            raise Exception('Already called: ' + self.cmd)

        from .console_script import console_script
        debug = console_script.options.get('debug', False)
        if debug is True or 'cmd' in str(debug):
            if self.prefix:
                print(f'{self.prefix} | + {self.cmd}')
            else:
                print(f'+ {self.cmd}')

        loop = asyncio.events.get_event_loop()
        transport, protocol = await loop.subprocess_exec(
            protocol_factory(self.prefix), *self.args)
        self.proc = asyncio.subprocess.Process(transport, protocol, loop)
        self.called = True

        if wait:
            await self.wait()

        return self

    async def communicate(self):
        self.out_raw, self.err_raw = await self.proc.communicate()
        self.out = self.out_raw.decode('utf8').strip()
        self.err = self.err_raw.decode('utf8').strip()
        self.rc = self.proc.returncode
        self.communicated = True
        return self

    async def wait(self):
        if not self.called:
            await self()
        if not self.communicated:
            await self.communicate()
        if self.raises and self.proc.returncode:
            raise WrongResult(self)
        return self

    @property
    def json(self):
        import json
        return json.loads(self.out)
