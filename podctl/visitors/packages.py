import os
import subprocess
from textwrap import dedent


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
        self.packages = list([
            dedent(l).strip().replace('\n', ' ') for l in packages
        ])
        self.mgr = kwargs.pop('mgr') if 'mgr' in kwargs else None
        if 'CACHE_DIR' in os.environ:
            self.cache = os.path.join(os.getenv('CACHE_DIR'), self.mgr)
        else:
            self.cache = os.path.join(os.getenv('HOME'), '.cache', self.mgr)

    async def pre_build(self, script):
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

    async def build(self, script):
        if not getattr(script.container, '_packages_upgraded', None):
            # run pkgmgr_setup functions ie. apk_setup
            await getattr(self, self.mgr + '_setup')(script)
            # first run on container means inject visitor packages
            self.packages += script.container.packages
            await script.run(self.cmds['upgrade'])
            script.container._packages_upgraded = True

        await script.run(' '.join([self.cmds['install']] + self.packages))

    async def apk_setup(self, script):
        await script.mount(self.cache, f'/var/cache/{self.mgr}')
        # special step to enable apk cache
        await script.run('ln -s /var/cache/apk /etc/apk/cache')
        await script.append(f'''
        old="$(find {self.cache} -name APKINDEX.* -mtime +3)"
        if [ -n "$old" ] || ! ls .cache/apk/APKINDEX.*; then
            {script._run(self.cmds['update'])}
        else
            echo Cache recent enough, skipping index update.
        fi
        ''')

    async def dnf_setup(self, script):
        await script.mount(self.cache, f'/var/cache/{self.mgr}')
        await script.run('sh -c "echo keepcache=True >> /etc/dnf/dnf.conf"')

    async def apt_setup(self, script):
        cache = self.cache + '/$(source $mnt/etc/os-release; echo $VERSION_CODENAME)/'  # noqa
        await script.run('sudo rm /etc/apt/apt.conf.d/docker-clean')
        cache_archives = os.path.join(self.cache, 'archives')
        await script.mount(cache_archives, f'/var/cache/apt/archives')
        cache_lists = os.path.join(self.cache, 'lists')
        await script.mount(cache_lists, f'/var/lib/apt/lists')
        await script.append(f'''
        old="$(find {cache_lists} -name lastup -mtime +3)"
        if [ -n "$old" ] || ! ls {cache_lists}/lastup; then
            until [ -z $(lsof /var/lib/dpkg/lock) ]; do sleep 1; done
            {script._run(self.cmds['update'])}
            touch {cache_lists}/lastup
        else
            echo Cache recent enough, skipping index update.
        fi
        ''')
