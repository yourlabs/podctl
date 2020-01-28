class Mount:
    def __init__(self, src, dst):
        self.src = src
        self.dst = dst

    def build(self, script):
        script.mount(self.src, self.dst)
