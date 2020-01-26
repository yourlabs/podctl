class Run:
    def __init__(self, *commands):
        self.commands = commands

    def build(self, script):
        for command in self.commands:
            for line in command.split('\n'):
                if line.strip():
                    script.run(line.strip())
