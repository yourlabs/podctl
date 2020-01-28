class Npm:
    def __init__(self, install=None):
        self.npm_install = install

    def build(self, script):
        script.append(f'cd {self.npm_install} && npm install')
