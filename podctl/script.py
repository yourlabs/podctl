import textwrap

from .proc import Proc


class Script:
    def __init__(self, name=None, doc=None):
        self.name = name or type(self).__name__.lower()
        self.doc = doc or 'Custom script'

    async def exec(self, *args, **kwargs):
        """Execute a command on the host."""
        kwargs.setdefault('prefix', self.container.name)
        proc = await Proc(*args, **kwargs)()
        if kwargs.get('wait', True):
            await proc.wait()
        return proc

    async def __call__(self, visitable, *args, **kwargs):
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

                print(
                    visitable.name + ' | ',
                    type(visitor).__name__,
                    method,
                    ' '.join(f'{k}={v}' for k, v in visitor.__dict__.items())
                )
                result = getattr(visitor, method)(self)
                if result:
                    try:
                        await result
                    except Exception as e:
                        await clean()
                        raise
