import subprocess


class Packages:
    mgrs = dict(
        apk=dict(
            update='sudo apk update',
            upgrade='sudo apk upgrade',
            install='sudo apk add',
        ),
    )

    def __init__(self, *packages):
        self.packages = list(packages)

    def pre_build(self, script):
        for mgr, cmds in self.mgrs.items():
            cmd = [
                'podman',
                'run',
                script.container.variable('base'),
                'which',
                mgr
            ]
            print('+ ' + ' '.join(cmd))
            try:
                subprocess.check_call(cmd)
                self.mgr = mgr
                self.cmds = cmds
                break
            except subprocess.CalledProcessError:
                continue

    def build(self, script):
        cache = f'.cache/{self.mgr}'
        script.mount(
            '$(pwd)/' + cache,
            f'/var/cache/{self.mgr}'
        )

        if self.mgr == 'apk':
            # special step to enable apk cache
            script.run('ln -s /var/cache/apk /etc/apk/cache')
            script.append(f'''
            old="$(find .cache/apk/ -name APKINDEX.* -mtime +3)"
            if [ -n "$old" ] || ! ls .cache/apk/APKINDEX.*; then
                {script._run(self.cmds['update'])}
            else
                echo Cache recent enough, skipping index update.
            fi
            ''')

        script.run(self.cmds['upgrade'])
        script.run(' '.join([self.cmds['install']] + self.packages))
