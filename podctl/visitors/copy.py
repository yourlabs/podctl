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

    def build(self, script):
        script.run(f'sudo mkdir -p {self.dst}')
        for item in self.src:
            script.append(f'cp -a {item} $mnt{self.dst}')

        if self.mode:
            script.run(f'sudo chmod {self.mode} $mnt{self.dst}')

        if self.owner:
            script.run(f'sudo chown -R {self.owner} $mnt{self.dst}')
