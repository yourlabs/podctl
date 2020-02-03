import re
import shlex

from .packages import Packages


class DumbInit:
    packages = ['dumb-init']

    def __init__(self, cmd):
        self.cmd = cmd

    def post_build(self, script):
        cmd = '--cmd "dumb-init bash -euxc \'%s\'"' % self.cmd
        script.config(cmd)
