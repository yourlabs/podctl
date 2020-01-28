class Npm:
    def __init__(self, install=None):
        self.npm_install = install

    def build(self, script):
        script.append('""')
