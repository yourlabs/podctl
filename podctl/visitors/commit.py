import os

CI_VARS = (
    # gitlab
    'CI_COMMIT_SHORT_SHA',
    'CI_COMMIT_REF_NAME',
    'CI_COMMIT_TAG',
    # CircleCI
    'CIRCLE_SHA1',
    'CIRCLE_TAG',
    'CIRCLE_BRANCH',
)


class Commit:
    def __init__(self, repo, tags=None, format=None, push=None):
        self.repo = repo
        self.format = format or 'oci'
        self.push = push
        self.tags = tags or []
        if self.repo.startswith('docker.io/'):
            self.format = 'docker'

        if not self.tags:
            for name in CI_VARS:
                value = os.getenv(name)
                if value:
                    self.tags.append(value)

        self.tags = [t for t in self.tags if t is not None]

    def post_build(self, script):
        creds = None
        '''
        if 'DOCKER_USER' in os.environ:
            creds = '--creds ' + os.getenv('DOCKER_USER')
            if 'DOCKER_PASS' in os.environ:
                creds += ':' + os.getenv('DOCKER_PASS')
        '''

        script.append(f'''
            umounts
            buildah commit --format={self.format} $ctr {self.repo}
        ''')

        if self.tags:
            script.append(f'buildah tag {self.repo} ' + ' '.join(self.tags))
