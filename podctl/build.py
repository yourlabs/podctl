import asyncio
import os
import subprocess
import textwrap

from .script import Script


class Build(Script):
    def __init__(self, container):
        super().__init__()
        self.container = container

    def append(self, value):
        res = []
        for line in value.split('\n'):
            if line.startswith('#') or not line.strip():
                continue
            res.append(self.unshare(line))
        return '\n'.join(res)

    async def unshare(self, line):
        print('+ buildah unshare ' + line)
        proc = await asyncio.create_subprocess_shell(
            'buildah unshare ' + line,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        ).decode('utf8')
        stdout, stderr = await proc.communicate()
        return stdout

    def config(self, line):
        self.append(f'buildah config {line} {self.ctr}')

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

    def run(self, cmd):
        self.append(self._run(cmd))

    def copy(self, src, dst):
        self.append(f'buildah copy {self.ctr} {src} {dst}')

    def mount(self, src, dst):
        self.run('sudo mkdir -p ' + dst)
        self.append('mkdir -p ' + src)
        self.append(f'mount -o bind {src} {self.mnt}{dst}')
        #self.append('mounts=("$mnt' + dst + '" "${mounts[@]}")')
        self.mounts.append((src, dst))

    def umounts(self):
        for src, dst in self.mounts:
            self.append('buildah unmount ' + dst)
        self.append('buildah unmount ' + self.ctr)
