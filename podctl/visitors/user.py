from .packages import Packages


class User:
    """Secure the image with a user"""
    packages = [
        'shadow',
    ]

    def __init__(self, username, uid, home):
        self.username = username
        self.uid = uid
        self.home = home
        self.user_created = False

    async def build(self, script):
        await script.append(f'''
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
