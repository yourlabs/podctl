from .packages import Packages


class User:
    """Secure the image with a user"""
    packages = dict(
        apk=['shadow'],
    )

    def __init__(self, username, uid, home, directories=None):
        self.username = username
        self.uid = uid
        self.home = home
        self.user_created = False
        self.directories = directories

    async def build(self, script):
        try:
            await script.cexec('id', self.uid)
        except:
            await script.cexec('useradd', '-d', self.home, '-u', self.uid, ' ',
                    self.username)
        else:
            await script.cexec('id', '-gn', self.uid)
        self.user_created = True

    def post_build(self, script):
        script.config(f'--user {self.username}')
