import asyncio
import os
import asyncio
import signal
import shlex
import subprocess
import textwrap

from .proc import Proc
from .script import Script


class Build(Script):
    def __init__(self, container):
        super().__init__()
        self.container = container
        self.log = []
        self.mounts = dict()

    async def config(self, line):
        return await self.append(f'buildah config {line} {self.ctr}')

    async def copy(self, src, dst):
        return await self.append(f'buildah copy {self.ctr} {src} {dst}')

    async def exec(self, *args, **kwargs):
        kwargs.setdefault('prefix', self.container.name)
        proc = await Proc(*args, **kwargs)()
        if kwargs.get('wait', True):
            await proc.wait()
        return proc

    async def cexec(self, *args, user=None, **kwargs):
        _args = ['buildah', 'run', self.ctr]
        if user:
            _args += ['--user', user]
        _args += ['--', 'sh', '-euc']
        return await self.exec(*(_args + list(args)))

    async def mount(self, src, dst):
        target = self.mnt / str(dst)[1:]
        await self.exec(f'mkdir -p {src} {target}')
        await self.exec(f'mount -o bind {src} {target}')
        self.mounts[src] = dst

    async def umounts(self):
        for src, dst in self.mounts.items():
            await self.exec('umount', self.mnt / str(dst)[1:])

    async def umount(self):
        await self.exec(f'buildah unmount {self.ctr}')

    def which(self, cmd):
        for path in self.container.paths:
            if os.path.exists(os.path.join(self.mnt, path[1:], cmd)):
                return True
