from textwrap import dedent


class Template:
    CMD = dedent(
        '''cat <<EOF > {target}
        {script}
        EOF'''
    )

    def __init__(self, target, *lines, **variables):
        self.target = target
        self.lines = lines
        self.variables = variables

    async def build(self, script):
        self.script = '\n'.join([
            dedent(l).strip() for l in self.lines
        ]).format(**self.variables)
        await script.cexec(self.CMD.strip().format(**self.__dict__))
        if self.script.startswith('#!'):
            await script.cexec('chmod +x ' + self.target, user='root')


class Append(Template):
    CMD = dedent(
        '''cat <<EOF >> {target}
        {script}
        EOF'''
    )
