class Cmd:
    def __init__(self, cmd):
        self.cmd = cmd

    def build(self, script):
        # script._run() does not really support sudo code
        script.run(self.cmd)
