import os


class Pip:
    def __init__(self, *pip_packages, pip=None):
        self.pip_packages = pip_packages
        self.pip = pip

    def build(self, script):
        if self.pip:
            script.append('_pip=' + self.pip)
        else:
            script.append(f'''
            if {script._run("bash -c 'type pip3'")}; then
                _pip=pip3
            elif {script._run("bash -c 'type pip'")}; then
                _pip=pip
            elif {script._run("bash -c 'type pip2'")}; then
                _pip=pip2
            fi
            ''')
        if 'CACHE_DIR' in os.environ:
            cache = os.path.join(os.getenv('CACHE_DIR'), 'pip')
        else:
            cache = os.path.join(os.getenv('HOME'), '.cache', 'pip')
        script.mount(cache, '/root/.cache/pip')
        script.run('sudo $_pip install --upgrade pip')
        source = [p for p in self.pip_packages if p.startswith('/')]
        if source:
            script.run(
                f'sudo $_pip install --upgrade --editable {" ".join(source)}'
            )

        nonsource = [p for p in self.pip_packages if not p.startswith('/')]
        if nonsource:
            script.run(f'sudo $_pip install --upgrade {" ".join(source)}')
