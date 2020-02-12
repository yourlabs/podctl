import os

from .script import Script
from .visitable import Visitable


class Pod(Visitable):
    def script_names(self):
        for name in self.scripts.keys():
            yield name

        for visitor in self.visitors:
            for script in visitor.scripts.keys():
                yield script

    def script(self, name):
        for script_name in self.scripts.keys():
            if script_name == name:
                break
        script.pod = self
        return script
