class Npm:
    def __init__(self, install=None):
        self.npm_install = install

    def build(self, script):
        script.run('sudo npm update -g npm')
        script.run(f'''
        cd {self.npm_install}
        npm install
        ''')
