from glob import glob
import inspect
import os
import subprocess
import time

from .script import Script


class BuildScript(Script):
    export = ('base', 'repo', 'tag', 'image')

    def __init__(self, container):
        super().__init__()
        self.container = container

        for var in self.export:
            if var in self.container:
                self.append(f'{var}="{self.container[var]}"')

        self.append('''
            mounts=()
            umounts() {
                for i in "${mounts[@]}"; do
                    umount $i
                done
            }
            trap umounts 0
            ctr=$(buildah from $base)
            mnt=$(buildah mount $ctr)
            mounts=("$mnt" "${mounts[@]}")
        ''')

        if self.container.get('packages'):
            self.container.packages_install(self)

    def config(self, line):
        self.append(f'buildah config {line} $ctr')

    def run(self, cmd):
        self.append('buildah run $ctr -- ' + cmd)

    def copy(self, src, dst):
        self.append(f'buildah copy $ctr {src} {dst}')

    def mount(self, src, dst):
        self.run('mkdir -p ' + dst)
        self.append('mkdir -p ' + src)
        self.append(f'mount -o bind {src} $mnt{dst}')
        # for unmount trap
        self.append('mounts=("$mnt%s" "${mounts[@]}")' % dst)


class Plugins(dict):
    def __init__(self, *plugins):
        default_plugins = [
            PkgPlugin(),
            UserPlugin(),
            FsPlugin(),
            BuildPlugin(),
            ConfigPlugin(),
        ]

        super().__init__()
        for plugin in plugins or default_plugins:
            self.add(plugin)

    def add(self, plugin):
        plugin.plugins = self
        self[plugin.name] = plugin

    def __call__(self, method, *args, **kwargs):
        hook = f'pre_{method}'
        for plugin in self.values():
            plugin(hook, *args, **kwargs)

        for plugin in self.values():
            if hasattr(plugin, method):
                plugin(method, *args, **kwargs)

        hook = f'post_{method}'
        for plugin in self.values():
            plugin(hook, *args, **kwargs)


class Plugin:
    @property
    def name(self):
        return type(self).__name__.replace('Plugin', '').lower()

    def bubble(self, hook, *args, **kwargs):
        for plugin in self.plugins.values():
            if plugin is self:
                continue
            plugin(hook, _bubble=False, *args, **kwargs)

    def __call__(self, method, *args, **kwargs):
        _bubble = kwargs.pop('_bubble', True)
        if _bubble:
            self.bubble(f'pre_{self.name}_{method}', *args, **kwargs)

        if hasattr(self, method):
            meth = getattr(self, method)
            argspec = inspect.getargspec(meth)
            if argspec.varargs and argspec.keywords:
                meth(*args, **kwargs)
            else:
                numargs = len(argspec.args) - 1 - len(argspec.defaults or [])
                args = args[:numargs]
                kwargs = {
                    k: v
                    for k, v in kwargs.items()
                    if k in argspec.args
                }
                meth(*args, **kwargs)

        if _bubble:
            self.bubble(f'post_{self.name}_{method}', *args, **kwargs)


class BuildPlugin(Plugin):
    def build(self, script):
        user = script.service.get('user', None)

        for cmd in script.service['build']:
            if cmd.startswith('sudo'):
                if user:
                    script.config(f'--user root')
                script.run(cmd[5:])
            else:
                script.config(f'--user {script.service["user"]}')
                script.run(cmd)


class FsPlugin(Plugin):
    def build(self, script):
        for key, value in script.service.items():
            if not key.startswith('/'):
                continue

            parts = key.split(':')
            dst = parts.pop(0)
            mode = parts.pop(0) if parts else '0500'
            script.run(f'mkdir -p {dst}')
            script.run(f'chmod {mode} $mnt{dst}')

            if value and isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        script.run(f'cp -a {item} $mnt{dst}')

                    if not isinstance(item, dict):
                        pass


class PkgPlugin(Plugin):
    mgrs = dict(
        apk=dict(
            update='apk update',
            upgrade='apk upgrade',
            install='apk add',
        ),
    )

    def pre_build(self, script):
        for mgr, cmds in self.mgrs.items():
            cmd = [
                'podman',
                'run',
                script.service['base'],
                'which',
                mgr
            ]
            print('+ ' + ' '.join(cmd))
            try:
                subprocess.check_call(cmd)
                script.service.mgr = mgr
                script.service.cmds = cmds
                break
            except subprocess.CalledProcessError:
                continue

    def build(self, script):
        cache = f'.cache/{script.service.mgr}'
        script.mount(
            '$(pwd)/' + cache,
            f'/var/cache/{script.service.mgr}'
        )

        cached = False
        if script.service.mgr == 'apk':
            # special step to enable apk cache
            script.run('ln -s /var/cache/apk /etc/apk/cache')
            for index in glob(cache + '/APKINDEX*'):
                if time.time() - os.stat(index).st_mtime < 3600:
                    cached = True
                    break

        if not cached:
            script.run(script.service.cmds['update'])

        script.run(script.service.cmds['upgrade'])
        script.run(' '.join([
            script.service.cmds['install'],
            ' '.join(script.service.get('packages', []))
        ]))


class ConfigPlugin(Plugin):
    def post_build(self, script):
        for value in script.service['ports']:
            script.config(f'--port {value}')

        for key, value in script.service['env'].items():
            script.config(f'--env {key}={value}')

        for key, value in script.service['labels'].items():
            script.config(f'--label {key}={value}')

        for key, value in script.service['annotations'].items():
            script.config(f'--annotation {key}={value}')

        for volume in script.service['volumes']:
            if ':' in volume:
                continue  # it's a runtime volume
            script.config(f'--volume {volume}')

        if 'workdir' in script.service:
            script.config(f'--workingdir {script.service["workdir"]}')


class UserPlugin(Plugin):
    def pre_pkg_build(self, script):
        if script.service.mgr == 'apk':
            script.service['packages'].append('shadow')

    def build(self, script):
        script.append(f'''
            if buildah run $ctr -- id {script.service['user']['id']}; then
                i=$(buildah run $ctr -- id -n {script.service['user']['id']})
                buildah run $ctr -- usermod -d {script.service['user']['home']} -l {script.service['user']['id']} $i
            else
                buildah run $ctr -- useradd -d {script.service['user']['home']} {script.service['user']['id']}
            fi
        ''')
