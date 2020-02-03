class Cmd:
    def __init__(self, cmd):
        self.cmd = cmd

    async def build(self, script):
        # script._run() does not really support sudo code
        await script.run(self.cmd)
