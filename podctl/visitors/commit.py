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

        # default tag by default ...
        if not self.tags:
            self.tags = ['latest']

    async def post_build(self, script):
        self.sha = (await script.exec(
            'buildah',
            'commit',
            '--format=' + self.format,
            script.ctr,
        )).out

        if 'master' in self.tags:
            self.tags.append('latest')

        if self.tags:
            tags = ' '.join([f'{self.repo}:{tag}' for tag in self.tags])
            await script.exec('buildah', 'tag', self.sha, self.repo, tags)

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

                for tag in self.tags:
                    await script.exec('podman', 'push', f'{self.repo}:{tag}')
        await script.umount()

    async def run(self, script):
        await script.exec(
            'podman', 'run', '-d',
            '--name', script.container.name,
            ':'.join((self.repo, self.tags[0])),
        )
