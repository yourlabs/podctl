import os
import subprocess

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
    def __init__(self, repo, tags=None, format=None, push=None, registry=None):
        self.repo = repo
        self.registry = registry
        self.push = push or os.getenv('CI')

        # figure out registry host
        if '/' in self.repo and not registry:
            first = self.repo.split('/')[0]
            if '.' in first or ':' in first:
                self.registry = self.repo.split('/')[0]

        # docker.io currently has issues with oci format
        self.format = format or 'oci'
        if self.registry == 'docker.io':
            self.format = 'docker'

        self.tags = tags or []

        # figure tags from CI vars
        if not self.tags:
            for name in CI_VARS:
                value = os.getenv(name)
                if value:
                    self.tags.append(value)

        # filter out tags which resolved to None
        self.tags = [t for t in self.tags if t is not None]

    def post_build(self, script):
        script.append(f'''
            umounts
            buildah commit --format={self.format} $ctr {self.repo}
        ''')

        if 'master' in self.tags:
            self.tags.append('latest')

        if self.tags:
            tags = ' '.join([f'{self.repo}:{tag}' for tag in self.tags])
            script.append(f'buildah tag {self.repo} {tags}')

            if self.push:
                user = os.getenv('DOCKER_USER')
                passwd = os.getenv('DOCKER_PASS')
                if user and passwd and os.getenv('CI') and self.registry:
                    subprocess.check_call([
                        'podman', 'login',
                        '-u', user, '-p', passwd,
                        self.registry
                    ])

                for tag in self.tags:
                    script.append(f'podman push {self.repo}:{tag}')
