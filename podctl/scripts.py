import asyncio
import cli2
import copy
import os
import sys

from .build import Build
from .exceptions import WrongResult
from .proc import output, Proc
from .script import Script


class Name(Script):
    color = cli2.GREEN

    async def run(self, *args, **kwargs):
        print(kwargs.get('pod').name)


class Down(Script):
    color = cli2.RED


class Up(Script):
    pass


class Run(Script):
    async def run(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        try:
            await self.exec(
                'podman', 'pod', 'inspect', self.pod.name
            )
            print(f'{self.pod.name} | Pod ready')
        except WrongResult:
            print(f'{self.pod.name} | Pod creating')
            await self.exec(
                'podman', 'pod', 'create', '--name', self.pod.name,
            )
            print(f'{self.pod.name} | Pod created')

        return await asyncio.gather(*[
            copy.deepcopy(self)(
                self.pod,
            )
            for container in self.pod.containers
        ])
