import textwrap

from .proc import Proc


class Script:
    async def exec(self, *args, **kwargs):
        """Execute a command on the host."""
        kwargs.setdefault('prefix', self.container.name)
        proc = await Proc(*args, **kwargs)()
        if kwargs.get('wait', True):
            await proc.wait()
        return proc

    async def __call__(self, name, loop=None):
        script = copy(self.scripts[name])
        script.loop = loop or asyncio.events.get_event_loop()
        results = []

        async def clean():
            for visitor in self.visitors:
                if hasattr(visitor, 'clean_' + name):
                    result = getattr(visitor, 'clean_' + name)(script)
                    if result:
                        await result

        for prefix in ('init_', 'pre_', '', 'post_', 'clean_'):
            method = prefix + name
            for visitor in self.visitors:
                if not hasattr(visitor, method):
                    continue

                rep = {k: v if not isinstance(v, object) else type(v).__name__ for k, v in visitor.__dict__.items()}
                print(self.name + ' | ', type(visitor).__name__, method, rep)
                result = getattr(visitor, method)(script)
                if result:
                    try:
                        await result
                    except Exception as e:
                        await clean()
                        raise
