import os
import subprocess

from ..exceptions import WrongResult

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
        self.registry = registry or 'localhost'
        self.push = push or os.getenv('CI')
        self.tags = tags or []

        # figure out registry host
        if '/' in self.repo and not registry:
            first = self.repo.split('/')[0]
            if '.' in first or ':' in first:
                self.registry = self.repo.split('/')[0]
                self.repo = '/'.join(self.repo.split('/')[1:])

        if ':' in self.repo and not tags:
            self.tags = [self.repo.split(':')[1]]
            self.repo = self.repo.split(':')[0]

        # docker.io currently has issues with oci format
        self.format = format or 'oci'
        if self.registry == 'docker.io':
            self.format = 'docker'

        # figure tags from CI vars
        if not self.tags:
            for name in CI_VARS:
                value = os.getenv(name)
                if value:
                    self.tags.append(value)

        # filter out tags which resolved to None
        self.tags = [t for t in self.tags if t is not None]

        # default tag by default ...
        if not self.tags:
            self.tags = ['latest']

        # default tag for master too
        if 'master' in self.tags:
            self.tags.append('latest')

        self.repotags = [f'{self.registry}/{self.repo}:{tag}' for tag in self.tags]

    async def post_build(self, script):
        self.sha = (await script.exec(
            'buildah',
            'commit',
            '--format=' + self.format,
            script.ctr,
        )).out

        if self.tags:
            for tag in self.repotags:
                await script.exec('buildah', 'tag', self.sha, self.repo, tag)

            if self.push:
                user = os.getenv('DOCKER_USER')
                passwd = os.getenv('DOCKER_PASS')
                if user and passwd and os.getenv('CI') and self.registry:
                    await script.exec(
                        'podman',
                        'login',
                        '-u',
                        user,
                        '-p',
                        passwd,
                        self.registry,
                    )

                for tag in self.repotags:
                    await script.exec('podman', 'push', tag)
        await script.umount()

    def __repr__(self):
        return f'Commit({self.registry}/{self.repo}:{self.tags})'
