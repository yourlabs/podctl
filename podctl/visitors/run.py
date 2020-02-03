class Run:
    def __init__(self, *commands):
        self.commands = commands

    async def build(self, script):
        for command in self.commands:
            await script.run(command)
