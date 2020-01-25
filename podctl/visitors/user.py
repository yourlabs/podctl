from .packages import Packages


class User:
    """Secure the image with a user"""

    def __init__(self, username, uid, home):
        self.username = username
        self.uid = uid
        self.home = home
        self.user_created = False

    def init_build(self, script):
        """Inject the Packages visitor if necessary."""
        packages = script.container.visitor('packages')
        if not packages:
            index = script.container.visitors.index(self)
            script.container.visitors.insert(index, Packages())

    def pre_build(self, script):
        """Inject the shadow package for the usermod command"""
        if script.container.variable('mgr') == 'apk':
            script.container.variable('packages').append('shadow')

    def build(self, script):
        script.append(f'''
            if buildah run $ctr -- id {self.uid}; then
                i=$(buildah run $ctr -- id -n {self.uid})
                buildah run $ctr -- usermod --home-dir {self.home} --no-log-init {self.uid} $i
            else
                buildah run $ctr -- useradd --home-dir {self.home} --uid {self.uid} {self.username}
            fi
        ''')  # noqa
        self.user_created = True

    def post_build(self, script):
        script.config(f'--user {self.username}')
