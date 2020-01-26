from .script import Script


class BuildScript(Script):
    export = ('base', 'repo')

    def __init__(self, container):
        super().__init__()
        self.container = container

        for var in self.export:
            self.append(f'{var}="{container.variable(var)}"')

        self.append('''
            mounts=()
            umounts() {
                for i in "${mounts[@]}"; do
                    umount $i
                    mounts=("${mounts[@]/$i}")
                done
                buildah unmount $ctr
                trap - 0
            }
            trap umounts 0
            ctr=$(buildah from $base)
            mnt=$(buildah mount $ctr)
        ''')

    def config(self, line):
        self.append(f'buildah config {line} $ctr')

    def _run(self, cmd):
        user = self.container.variable('username')
        if cmd.startswith('sudo '):
            return f'buildah run --user root $ctr -- {cmd[5:]}'
        elif user and self.container.variable('user_created'):
            return f'buildah run --user {user} $ctr -- {cmd}'
        else:
            return f'buildah run $ctr -- {cmd}'

    def run(self, cmd):
        self.append(self._run(cmd))

    def copy(self, src, dst):
        self.append(f'buildah copy $ctr {src} {dst}')

    def mount(self, src, dst):
        self.run('sudo mkdir -p ' + dst)
        self.append('mkdir -p ' + src)
        self.append(f'mount -o bind {src} $mnt{dst}')
