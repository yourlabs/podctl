import asyncio
import cli2
import textwrap

from .proc import Proc


class Script:
    options = [
        cli2.Option(
            'debug',
            alias='d',
            color=cli2.GREEN,
            help='''
            Display debug output.
            Supports values: proc,out,visit
            '''
        ),
    ]

    def __init__(self, name=None, doc=None):
        self.name = name or type(self).__name__.lower()
        self.doc = doc or 'Custom script'

    async def exec(self, *args, **kwargs):
        """Execute a command on the host."""
        if getattr(self, 'container', None):
            kwargs.setdefault('prefix', self.container.name)
        proc = await Proc(*args, **kwargs)()
        if kwargs.get('wait', True):
            await proc.wait()
        return proc

    async def __call__(self, visitable, *args, **kwargs):
        from .console_script import console_script
        debug = console_script.parser.options.get('debug', False)

        for key, value in kwargs.items():
            setattr(self, key, value)

        visitors = visitable.visitors

        results = []
        async def clean():
            for visitor in visitable.visitors:
                if hasattr(visitor, 'clean_' + self.name):
                    result = getattr(visitor, 'clean_' + self.name)(self)
                    if result:
                        await result

        for prefix in ('init_', 'pre_', '', 'post_', 'clean_'):
            method = prefix + self.name
            for visitor in visitable.visitors:
                if not hasattr(visitor, method):
                    continue

                if debug is True or 'visit' in str(debug):
                    print(
                        visitable.name + ' | ',
                        '.'.join([type(visitor).__name__, method]),
                        ' '.join(f'{k}={v}' for k, v in visitor.__dict__.items())
                    )
                result = getattr(visitor, method)(self)
                if result:
                    try:
                        await result
                    except Exception as e:
                        await clean()
                        raise

    async def run(self, *args, **kwargs):
        pod = kwargs.get('pod')

        if args:
            containers = [c for c in pod.containers if c.name in args]
        else:
            containers = pod.containers

        procs = []
        for container in containers:
            procs.append(self(
                container,
                *args,
                container=container,
                **kwargs,
            ))

        return await asyncio.gather(*procs)
