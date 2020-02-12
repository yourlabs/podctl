import asyncio
import os
import shlex

from .build import Build
from .run import Run
from .visitable import Visitable


class Container(Visitable):
    default_scripts = dict(
        build=Build(),
        run=Run(),
    )

    def script(self, name):
        script = super().script(name)
        script.container = self
        return script
