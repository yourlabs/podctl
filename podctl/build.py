import asyncio
import os
import asyncio
import signal
import shlex
import subprocess
import sys
import textwrap

from .proc import Proc, output
from .script import Script


class Build(Script):
    """
    The build script iterates over visitors and runs the build functions, it
    also provides wrappers around the buildah command.
    """
    unshare = True

    def __init__(self):
        super().__init__()
        self.mounts = dict()
        self.ctr = None
        self.mnt = None

    async def config(self, line):
        """Run buildah config."""
        return await self.exec(f'buildah config {line} {self.ctr}')

    async def copy(self, src, dst):
        """Run buildah copy to copy a file from host into container."""
        return await self.exec(f'buildah copy {self.ctr} {src} {dst}')

    async def cexec(self, *args, user=None, **kwargs):
        """Execute a command in the container."""
        _args = ['buildah', 'run']
        if user:
            _args += ['--user', user]
        _args += [self.ctr, '--', 'sh', '-euc']
        return await self.exec(*(_args + [' '.join([str(a) for a in args])]))

    async def crexec(self, *args, **kwargs):
        """Execute a command in the container as root."""
        kwargs['user'] = 'root'
        return await self.cexec(*args, **kwargs)

    async def mount(self, src, dst):
        """Mount a host directory into the container."""
        target = self.mnt / str(dst)[1:]
        await self.exec(f'mkdir -p {src} {target}')
        await self.exec(f'mount -o bind {src} {target}')
        self.mounts[src] = dst

    async def umounts(self):
        """Unmount all mounted directories from the container."""
        for src, dst in self.mounts.items():
            await self.exec('umount', self.mnt / str(dst)[1:])

    async def umount(self):
        """Unmount the buildah container with buildah unmount."""
        if self.ctr:
            await self.exec(f'buildah unmount {self.ctr}')

    async def paths(self):
        """Return the list of $PATH directories"""
        return (await self.cexec('echo $PATH')).out.split(':')

    async def which(self, cmd):
        """
        Return the first path to the cmd in the container.

        If cmd argument is a list then it will try all commands.
        """
        if not isinstance(cmd, (list, tuple)):
            cmd = [cmd]

        for path in await self.paths():
            for c in cmd:
                p = os.path.join(self.mnt, path[1:], c)
                if os.path.exists(p):
                    return p[len(str(self.mnt)):]

    def __repr__(self):
        return f'Build'

    async def run(self, *args, **kwargs):
        if os.getuid() == 0:
            return await super().run(*args, **kwargs)

        from podctl.console_script import console_script
        # restart under buildah unshare environment !
        argv = [
            'buildah', 'unshare',
            sys.argv[0],  # current podctl location
        ]
        if console_script.options.get('debug') is True:
            argv.append('-d')
        elif isinstance(console_script.options.get('debug'), str):
            argv.append('-d=' + console_script.options.get('debug'))
        argv += [
            type(self).__name__.lower(),  # script name ?
        ]
        output(' '.join(argv), 'EXECUTION', flush=True)

        proc = await asyncio.create_subprocess_shell(
            shlex.join(argv),
            stderr=sys.stderr,
            stdin=sys.stdin,
            stdout=sys.stdout,
        )
        await proc.communicate()
        console_script.exit_code = proc.returncode
        return
        pp = subprocess.Popen(
            argv,
            stderr=sys.stderr,
            stdin=sys.stdin,
            stdout=sys.stdout,
        )
        pp.communicate()
        console_script.exit_code = pp.returncode
