import asyncio

from datetime import datetime
from glob import glob
import os
import subprocess
from textwrap import dedent


class Packages:
    mgrs = dict(
        apk=dict(
            update='apk update',
            upgrade='apk upgrade',
            install='apk add',
        ),
        apt=dict(
            update='apt-get -y update',
            upgrade='apt-get -y upgrade',
            install='apt-get -y --no-install-recommends install',
        ),
        dnf=dict(
            update='dnf update',
            upgrade='dnf upgrade --exclude container-selinux --best --assumeyes',  # noqa
            install='dnf install --exclude container-selinux --setopt=install_weak_deps=False --best --assumeyes',  # noqa
        ),
        yum=dict(
            update='yum update',
            upgrade='yum upgrade',
            install='yum install',
        ),
    )

    def __init__(self, *packages, **kwargs):
        self.packages = list([
            dedent(l).strip().replace('\n', ' ') for l in packages
        ])
        self.mgr = kwargs.pop('mgr') if 'mgr' in kwargs else None

    @property
    def cache(self):
        if 'CACHE_DIR' in os.environ:
            return os.path.join(os.getenv('CACHE_DIR'), self.mgr)
        else:
            return os.path.join(os.getenv('HOME'), '.cache', self.mgr)

    async def init_build(self, script):
        paths = ('bin', 'sbin', 'usr/bin', 'usr/sbin')
        for mgr, cmds in self.mgrs.items():
            for path in paths:
                if (script.mnt / path / mgr).exists():
                    self.mgr = mgr
                    self.cmds = cmds
                    break
        if not self.mgr:
            raise Exception('Packages does not yet support this distro')

    async def build(self, script):
        if not getattr(script.container, '_packages_upgraded', None):
            # run pkgmgr_setup functions ie. apk_setup
            await getattr(self, self.mgr + '_setup')(script)
            # first run on container means inject visitor packages
            self.packages += script.container.packages
            await script.cexec(self.cmds['upgrade'])
            script.container._packages_upgraded = True

        await script.cexec(' '.join([self.cmds['install']] + self.packages))

    async def apk_setup(self, script):
        await script.mount(self.cache, f'/var/cache/{self.mgr}')
        # special step to enable apk cache
        await script.cexec('ln -s /var/cache/apk /etc/apk/cache')

        # do we have to update ?
        update = False
        for f in glob(self.cache + '/APKINDEX*'):
            mtime = os.stat(f).st_mtime
            now = int(datetime.now().strftime('%s'))
            # expect hacker to have internet at least once a week
            if now - mtime > 604800:
                update = True
                break
        else:
            update = True

        if update:
            await self.apk_update(script)

    async def apk_update(self, script):
        while os.path.exists(self.cache + '/update'):
            print(f'{script.container.name} | Waiting for update ...')
            await asyncio.sleep(1)
            return  # update was done by another job

        with open(self.cache + '/update', 'w+') as f:
            f.write(str(os.getpid()))

        try:
            await script.cexec(self.cmds['update'])
        except:
            raise
        finally:
            os.unlink(self.cache + '/update')

    async def dnf_setup(self, script):
        await script.mount(self.cache, f'/var/cache/{self.mgr}')
        await script.run('echo keepcache=True >> /etc/dnf/dnf.conf')

    async def apt_setup(self, script):
        cache = self.cache + '/$(source $mnt/etc/os-release; echo $VERSION_CODENAME)/'  # noqa
        await script.run('rm /etc/apt/apt.conf.d/docker-clean')
        cache_archives = os.path.join(self.cache, 'archives')
        await script.mount(cache_archives, f'/var/cache/apt/archives')
        cache_lists = os.path.join(self.cache, 'lists')
        await script.mount(cache_lists, f'/var/lib/apt/lists')

        await script.run(self.cmds['update'])
        """
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
        """
