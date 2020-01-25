class Run:
    def __init__(self, *commands):
        self.commands = commands

    def build(self, script):
        for command in self.commands:
            script.run(command)
