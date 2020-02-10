from pathlib import Path


class Base:
    def __init__(self, base):
        self.base = base

    async def init_build(self, script):
        script.ctr = Path((await script.exec('buildah', 'from', self.base)).out)
        script.mnt = Path((await script.exec('buildah', 'mount', script.ctr)).out)

    async def post_build(self, script):
        await script.umounts()
