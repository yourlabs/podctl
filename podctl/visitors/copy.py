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
        await script.run(f'sudo mkdir -p {self.dst}')
        for item in self.src:
            await script.append(f'cp -a {item} $mnt{self.dst}')

        if self.mode:
            await script.run(f'sudo chmod {self.mode} $mnt{self.dst}')

        if self.owner:
            await script.run(f'sudo chown -R {self.owner} $mnt{self.dst}')
