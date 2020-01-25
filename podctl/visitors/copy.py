class Copy:
    def __init__(self, src, dst):
        self.src = src
        self.dst = dst

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
        if isinstance(self.src, list):
            script.run(f'sudo mkdir -p {self.dst}')
            for item in self.src:
                script.append(f'cp -a {item} $mnt{self.dst}')

        if self.mode:
            script.run(f'sudo chmod {self.mode} $mnt{self.dst}')

        if self.owner:
            script.run(f'sudo chown -R {self.owner} $mnt{self.dst}')
