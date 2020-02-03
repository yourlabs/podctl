import asyncio
import os
import asyncio
import signal
import subprocess
import textwrap

from .script import Script


class WrongResult(Exception):
    pass


class Build(Script):
    def __init__(self, container):
        super().__init__()
        self.container = container
        self.log = []
        self.mounts = dict()

    async def cmd(self, line):
        log = dict(cmd=line)
        self.log.append(log)
        line = self.unshare(line)
        print(self.container.name + ' | ' + line)
        def protocol_factory():
            from .console_script import BuildStreamProtocol
            return BuildStreamProtocol(
                self.container,
                limit=asyncio.streams._DEFAULT_LIMIT,
                loop=self.loop,
            )
        transport, protocol = await self.loop.subprocess_shell(
            protocol_factory,
            line,
        )
        proc = asyncio.subprocess.Process(
            transport,
            protocol,
            self.loop,
        )
        result = await proc.wait()
        if result:
            raise WrongResult(proc)
        return proc
        '''
        proc = await asyncio.create_subprocess_shell(
            line,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        '''

    async def append(self, value):
        for line in value.split('\n'):
            if line.startswith('#') or not line.strip():
                continue
            log = dict(proc=await self.cmd(line))
            log['stdout'], log['stderr'] = await log['proc'].communicate()

        return log['stdout']

    def unshare(self, line):
        return 'buildah unshare ' + line

    async def config(self, line):
        return await self.append(f'buildah config {line} {self.ctr}')

    def _run(self, cmd, inject=False):
        user = self.container.variable('username')
        _cmd = textwrap.dedent(cmd)
        if cmd.startswith('sudo '):
            _cmd = _cmd[5:]

        heredoc = False
        for i in ('\n', '>', '<', '|', '&'):
            if i in _cmd:
                heredoc = True
                break

        if heredoc:
            _cmd = ''.join(['bash -eux <<__EOF\n', _cmd.strip(), '\n__EOF'])

        if cmd.startswith('sudo '):
            return f'buildah run --user root {self.ctr} -- {_cmd}'
        elif user and self.container.variable('user_created'):
            return f'buildah run --user {user} {self.ctr} -- {_cmd}'
        else:
            return f'buildah run {self.ctr} -- {_cmd}'

    async def run(self, cmd):
        return await self.append(self._run(cmd))

    async def copy(self, src, dst):
        return await self.append(f'buildah copy {self.ctr} {src} {dst}')

    async def mount(self, src, dst):
        await self.run('sudo mkdir -p ' + dst)
        await self.append('mkdir -p ' + src)
        await self.append(f'mount -o bind {src} {self.mnt}{dst}')
        #await self.append('mounts=("$mnt' + dst + '" "${mounts[@]}")')
        self.mounts[dst] = src

    async def umounts(self):
        for src, dst in self.mounts:
            await self.append('buildah unmount ' + dst)
        await self.append('buildah unmount ' + self.ctr)

    def which(self, cmd):
        for path in self.container.paths:
            if os.path.exists(os.path.join(path, cmd)):
                return True
