class Npm:
    def __init__(self, install=None):
        self.npm_install = install

    async def build(self, script):
        await script.run('sudo npm update -g npm')
        await script.run(f'''
        cd {self.npm_install}
        npm install
        ''')
