from glob import glob
import os


class Pip:
    def __init__(self, *pip_packages, pip=None, requirements=None):
        self.pip_packages = pip_packages
        self.pip = pip
        self.requirements = requirements

    async def build(self, script):
        for pip in ('pip3', 'pip', 'pip2'):
            if script.which(pip):
                self.pip = pip
                break

        if 'CACHE_DIR' in os.environ:
            cache = os.path.join(os.getenv('CACHE_DIR'), 'pip')
        else:
            cache = os.path.join(os.getenv('HOME'), '.cache', 'pip')

        await script.mount(cache, '/root/.cache/pip')
        await script.run(f'sudo {self.pip} install --upgrade pip')
        source = [p for p in self.pip_packages if p.startswith('/')]
        if source:
            await script.run(
                f'sudo {self.pip} install --upgrade --editable {" ".join(source)}'
            )

        nonsource = [p for p in self.pip_packages if not p.startswith('/')]
        if nonsource:
            await script.run(f'sudo {self.pip} install --upgrade {" ".join(source)}')

        if self.requirements:
            await script.run(f'sudo {self.pip} install --upgrade -r {self.requirements}')
