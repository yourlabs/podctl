import subprocess


class Packages:
    mgrs = dict(
        apk=dict(
            update='sudo apk update',
            upgrade='sudo apk upgrade',
            install='sudo apk add',
        ),
        dnf=dict(
            update='sudo dnf update',
            upgrade='sudo dnf upgrade --exclude container-selinux --best --assumeyes',
            install='sudo dnf install --exclude container-selinux --setopt=install_weak_deps=False --best --assumeyes',  # noqa
        ),
        yum=dict(
            update='sudo yum update',
            upgrade='sudo yum upgrade',
            install='sudo yum install',
        ),
    )

    def __init__(self, *packages, **kwargs):
        self.packages = list(packages)
        self.mgr = kwargs.pop('mgr')

    def pre_build(self, script):
        base = script.container.variable('base')
        if self.mgr:
            self.cmds = self.mgrs[self.mgr]
        else:
            for mgr, cmds in self.mgrs.items():
                cmd = ['podman', 'run', base, 'sh', '-c', f'type {mgr}']
                try:
                    subprocess.check_call(cmd)
                    self.mgr = mgr
                    self.cmds = cmds
                    break
                except subprocess.CalledProcessError:
                    continue
        if not self.mgr:
            raise Exception('Packages does not yet support this distro')

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
        elif self.mgr == 'dnf':
            script.run('sh -c "echo keepcache=True >> /etc/dnf/dnf.conf"')

        script.run(self.cmds['upgrade'])
        script.run(' '.join([self.cmds['install']] + self.packages))
