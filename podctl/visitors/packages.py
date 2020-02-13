import asyncio
import copy

from datetime import datetime
from glob import glob
import os
import subprocess
from textwrap import dedent


class Packages:
    """
    The Packages visitor wraps around the container's package manager.

    It's a central piece of the build process, and does iterate over other
    container visitors in order to pick up packages. For example, the Pip
    visitor will declare ``self.packages = dict(apt=['python3-pip'])``, and the
    Packages visitor will pick it up.
    """
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

    installed = []

    def __init__(self, *packages, **kwargs):
        self.packages = []

        for package in packages:
            line = dedent(package).strip().replace('\n', ' ')
            self.packages += line.split(' ')

        self.mgr = kwargs.pop('mgr') if 'mgr' in kwargs else None

    @property
    def cache_root(self):
        if 'CACHE_DIR' in os.environ:
            return os.path.join(os.getenv('CACHE_DIR'))
        else:
            return os.path.join(os.getenv('HOME'), '.cache')

    async def init_build(self, script):
        cached = script.container.variable('mgr')
        if cached:
            self.mgr = cached
        else:
            for mgr, cmds in self.mgrs.items():
                if await script.which(mgr):
                    self.mgr = mgr
                    break

        if not self.mgr:
            raise Exception('Packages does not yet support this distro')

        self.cmds = self.mgrs[self.mgr]

    async def update(self, script):
        # run pkgmgr_setup functions ie. apk_setup
        cachedir = await getattr(self, self.mgr + '_setup')(script)

        lastupdate = None
        if os.path.exists(cachedir + '/lastupdate'):
            with open(cachedir + '/lastupdate', 'r') as f:
                try:
                    lastupdate = int(f.read().strip())
                except:
                    pass

        now = int(datetime.now().strftime('%s'))
        # cache for a week
        if not lastupdate or now - lastupdate > 604800:
            # crude lockfile implementation, should work against *most*
            # race-conditions ...
            lockfile = cachedir + '/update.lock'
            if not os.path.exists(lockfile):
                with open(lockfile, 'w+') as f:
                    f.write(str(os.getpid()))

                try:
                    await script.cexec(self.cmds['update'])
                finally:
                    os.unlink(lockfile)

                with open(cachedir + '/lastupdate', 'w+') as f:
                    f.write(str(now))
            else:
                while os.path.exists(lockfile):
                    print(f'{script.container.name} | Waiting for update ...')
                    await asyncio.sleep(1)

    async def build(self, script):
        if not getattr(script.container, '_packages_upgraded', None):
            await self.update(script)
            await script.cexec(self.cmds['upgrade'])

            # first run on container means inject visitor packages
            packages = []
            for visitor in script.container.visitors:
                pp = getattr(visitor, 'packages', None)
                if pp:
                    if isinstance(pp, list):
                        packages += pp
                    elif self.mgr in pp:
                        packages += pp[self.mgr]

            script.container._packages_upgraded = True
        else:
            packages = self.packages

        await script.crexec(*self.cmds['install'].split(' ') + packages)

    async def apk_setup(self, script):
        cachedir = os.path.join(self.cache_root, self.mgr)
        await script.mount(cachedir, '/var/cache/apk')
        # special step to enable apk cache
        await script.cexec('ln -s /var/cache/apk /etc/apk/cache')
        return cachedir

    async def dnf_setup(self, script):
        cachedir = os.path.join(self.cache_root, self.mgr)
        await script.mount(cachedir, f'/var/cache/{self.mgr}')
        await script.run('echo keepcache=True >> /etc/dnf/dnf.conf')

    async def apt_setup(self, script):
        codename = (await script.exec(
            f'source {script.mnt}/etc/os-release; echo $VERSION_CODENAME'
        )).out
        cachedir = os.path.join(self.cache_root, self.mgr, codename)
        await script.cexec('rm /etc/apt/apt.conf.d/docker-clean')
        cache_archives = os.path.join(cachedir, 'archives')
        await script.mount(cache_archives, f'/var/cache/apt/archives')
        cache_lists = os.path.join(cachedir, 'lists')
        await script.mount(cache_lists, f'/var/lib/apt/lists')
        return cachedir

    def __repr__(self):
        return f'Packages({self.packages})'
