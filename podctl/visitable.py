from copy import copy


class Visitable:
    default_scripts = dict()

    def __init__(self, *visitors, **scripts):
        self.visitors = list(visitors)
        self.scripts = scripts or {
            k: v(self) for k, v in self.default_scripts.items()
        }

    def script(self, name):
        script = copy(self.scripts[name])

        for prefix in ('init_', 'pre_', '', 'post_'):
            method = prefix + name
            for visitor in self.visitors:
                if hasattr(visitor, method):
                    script.append(f'echo "{type(visitor).__name__}.{method}"')
                    getattr(visitor, method)(script)

        return script

    def visitor(self, name):
        for visitor in self.visitors:
            if name.lower() == type(visitor).__name__.lower():
                return visitor

    def variable(self, name):
        for visitor in self.visitors:
            if getattr(visitor, name, None) is not None:
                return getattr(visitor, name)
