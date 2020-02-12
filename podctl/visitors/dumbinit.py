import re
import shlex

from .packages import Packages


class DumbInit:
    packages = ['dumb-init']

    def __init__(self, cmd):
        self.cmd = cmd

    async def post_build(self, script):
        cmd = '--cmd "dumb-init bash -euxc \'%s\'"' % self.cmd
        await script.config(cmd)

    def __repr__(self):
        return f'DumbInit({self.cmd})'
