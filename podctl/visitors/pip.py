class Pip:
    def __init__(self, *pip_packages):
        self.pip_packages = pip_packages

    def build(self, script):
        script.append(f'''
        if {script._run("bash -c 'type pip3'")}; then
            _pip=pip3
        elif {script._run("bash -c 'type pip'")}; then
            _pip=pip
        elif {script._run("bash -c 'type pip2'")}; then
            _pip=pip2
        fi
        ''')
        script.mount('.cache/pip', '/root/.cache/pip')
        script.run('sudo $_pip install --upgrade pip')
        source = [p for p in self.pip_packages if p.startswith('/')]
        if source:
            script.run(
                f'sudo $_pip install --upgrade --editable {" ".join(source)}'
            )

        nonsource = [p for p in self.pip_packages if not p.startswith('/')]
        if nonsource:
            script.run(f'sudo $_pip install --upgrade {" ".join(source)}')
