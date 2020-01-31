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
            if {script._run('id ' + str(self.uid))}; then
                i=$({script._run('id -gn ' + str(self.uid))})
                {script._run('usermod -d ' + self.home + ' -l ' + self.username + ' $i')}
            else
                {script._run('useradd -d ' + self.home + ' -u ' + str(self.uid) + ' ' + self.username)}
            fi
        ''')  # noqa
        self.user_created = True

    def post_build(self, script):
        script.config(f'--user {self.username}')
