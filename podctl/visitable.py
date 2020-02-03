from copy import copy


class Visitable:
    default_scripts = dict()

    def __init__(self, *visitors, **scripts):
        self.visitors = list(visitors)
        self.scripts = scripts or {
            k: v(self) for k, v in self.default_scripts.items()
        }

    async def script(self, name, loop):
        script = copy(self.scripts[name])
        script.loop = loop
        results = []

        for prefix in ('init_', 'pre_', '', 'post_'):
            method = prefix + name
            for visitor in self.visitors:
                if not hasattr(visitor, method):
                    continue

                rep = {k: v if not isinstance(v, object) else type(v).__name__ for k, v in visitor.__dict__.items()}
                print(self.name + ' | ', type(visitor).__name__, method, rep)
                result = getattr(visitor, method)(script)
                if result:
                    await result


    def visitor(self, name):
        for visitor in self.visitors:
            if name.lower() == type(visitor).__name__.lower():
                return visitor

    def variable(self, name):
        for visitor in self.visitors:
            if getattr(visitor, name, None) is not None:
                return getattr(visitor, name)
