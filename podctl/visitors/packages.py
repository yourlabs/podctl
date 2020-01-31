import os
import subprocess


class Packages:
    mgrs = dict(
        apk=dict(
            update='sudo apk update',
            upgrade='sudo apk upgrade',
            install='sudo apk add',
        ),
        apt=dict(
            update='sudo apt-get -y update',
            upgrade='sudo apt-get -y upgrade',
            install='sudo apt-get -y --no-install-recommends install',
        ),
        dnf=dict(
            update='sudo dnf update',
            upgrade='sudo dnf upgrade --exclude container-selinux --best --assumeyes',  # noqa
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
        self.mgr = kwargs.pop('mgr') if 'mgr' in kwargs else None

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
        if 'CACHE_DIR' in os.environ:
            cache = os.path.join(os.getenv('CACHE_DIR'), self.mgr)
        else:
            cache = os.path.join(os.getenv('HOME'), '.cache', self.mgr)

        if self.mgr == 'apk':
            script.mount(cache, f'/var/cache/{self.mgr}')
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
            script.mount(cache, f'/var/cache/{self.mgr}')
            script.run('sh -c "echo keepcache=True >> /etc/dnf/dnf.conf"')
        elif self.mgr == 'apt':
            script.run('sudo rm /etc/apt/apt.conf.d/docker-clean')
            cache_archives = os.path.join(cache, 'archives')
            script.mount(cache_archives, f'/var/cache/apt/archives')
            cache_lists = os.path.join(cache, 'lists')
            script.mount(cache_lists, f'/var/lib/apt/lists')
            script.append(f'''
            old="$(find {cache_lists} -name lastup -mtime +3)"
            if [ -n "$old" ] || ! ls {cache_lists}/lastup; then
                {script._run(self.cmds['update'])}
                touch {cache_lists}/lastup
            else
                echo Cache recent enough, skipping index update.
            fi
            ''')
        script.run(self.cmds['upgrade'])
        script.run(' '.join([self.cmds['install']] + self.packages))
