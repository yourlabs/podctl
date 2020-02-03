class Mount:
    def __init__(self, src, dst):
        self.src = src
        self.dst = dst

    async def build(self, script):
        await script.mount(self.src, self.dst)
