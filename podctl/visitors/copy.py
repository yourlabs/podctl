class Copy:
    def __init__(self, *args):
        self.src = args[:-1]
        self.dst = args[-1]

    def init_build(self, script):
        count = self.dst.count(':')
        self.mode = None
        self.owner = None
        if count == 2:
            self.dst, self.mode, self.owner = self.dst.split(':')
        elif count == 1:
            self.dst, self.mode = self.dst.split(':')
            self.owner = script.variable('user')

    async def build(self, script):
        await script.crexec(f'mkdir -p {self.dst}')
        for item in self.src:
            await script.exec(f'cp -a {item} {script.mnt}{self.dst}')

        if self.mode:
            await script.crexec(f'chmod {self.mode} {script.mnt}{self.dst}')

        if self.owner:
            await script.crexec(f'chown -R {self.owner} {script.mnt}{self.dst}')
