

class Base:
    def __init__(self, base):
        self.base = base

    async def init_build(self, script):
        ctr = await script.cmd('buildah from ' + self.base)
        stdout, stderr = await ctr.communicate()
        script.ctr = stdout.decode('utf8').strip()
        mnt = await script.cmd('buildah mount ' + script.ctr)
        stdout, stderr = await mnt.communicate()
        script.mnt = stdout.decode('utf8').strip()
