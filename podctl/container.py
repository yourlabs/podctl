import collections
import copy
from glob import glob
import subprocess

from .build import BuildScript


PACKAGE_MANAGERS = dict(
    apk=dict(
        update='apk update',
        upgrade='apk upgrade',
        install='apk add',
    ),
)


class Container(collections.UserDict):
    cfg = dict()

    def __init__(self, profile=None, **cfg):
        newcfg = copy.deepcopy(self.cfg)
        newcfg.update(cfg)
        super().__init__(**newcfg)
        self.profile = profile or 'default'

    def __getitem__(self, name, type=None):
        try:
            result = super().__getitem__(name)
        except KeyError:
            if hasattr(self, name + '_get'):
                result = self[name] = getattr(self, name + '_get')()
            else:
                raise
        else:
            if isinstance(result, (dict, list, tuple, switch)):
                return self.switch_value(result)
        return result

    def switch_value(self, value):
        _switch = lambda v: v.value(self) if isinstance(v, switch) else v

        if isinstance(value, dict):
            return {
                k: self.switch_value(v)
                for k, v in value.items()
                if self.switch_value(v) is not None
            }
        elif isinstance(value, (list, tuple)):
            return [
                self.switch_value(i)
                for i in value
                if self.switch_value(i) is not None
            ]
        else:
            return _switch(value)

    def script_build(self):
        return BuildScript(self)

    def package_manager_get(self):
        for mgr in PACKAGE_MANAGERS.keys():
            cmd = ['podman', 'run', self['base'], 'which', mgr]
            try:
                subprocess.check_call(cmd)
                return mgr
                break
            except subprocess.CalledProcessError:
                continue
        raise Exception('Package manager not supported yet')

    def package_manager_cmd(self, cmd):
        return PACKAGE_MANAGERS[self['package_manager']][cmd]

    def packages_install(self, script):
        cache = f'.cache/{self["package_manager"]}'
        script.mount(
            '$(pwd)/' + cache,
            f'/var/cache/{self["package_manager"]}'
        )

        cached = False
        if self['package_manager'] == 'apk':
            # special step to enable apk cache
            script.run('ln -s /var/cache/apk /etc/apk/cache')
            script.append(f'''
            if [ -n "$(find .cache/apk/ -name APKINDEX.* -mtime +3)" ]; then
                buildah run $ctr -- {self.package_manager_cmd("update")}
            fi
            ''')

        script.run(self.package_manager_cmd('upgrade'))
        script.run(' '.join([
            self.package_manager_cmd('install'),
            ' '.join(self.get('packages', []))
        ]))


class switch:
    def __init__(self, **values):
        """Instanciate a switch to vary values based on container profile."""
        self.values = values

    def value(self, container):
        """Return value from container profile or default."""
        return self.values.get(
            container.profile,
            self.values.get('default', None)
        )
