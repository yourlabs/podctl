from textwrap import dedent


CMD = '''cat <<EOF > {target}
{script}
EOF'''

class Template:
    def __init__(self, target, *lines, **variables):
        self.target = target
        self.lines = lines
        self.variables = variables

    def build(self, script):
        self.script = '\n'.join([
            dedent(l).strip() for l in self.lines
        ]).format(**self.variables)
        script.run(CMD.strip().format(**self.__dict__))
        if self.script.startswith('#!'):
            script.run('sudo chmod +x ' + self.target)
