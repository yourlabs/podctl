import textwrap


class Script(list):
    def __init__(self, shebang=None):
        super().__init__()
        self.append(shebang or '#/usr/bin/env bash')

    def __str__(self):
        if not getattr(self, '_postconfig', False):
            if hasattr(self, 'post_config'):
                self.post_config()
            self._postconfig = True
        return '\n'.join([
            textwrap.dedent(line.lstrip('\n')).strip()
            for line in self
        ])
