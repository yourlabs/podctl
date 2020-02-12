import importlib

from .container import Container
from .pod import Pod


class Podfile:
    def __init__(self, pods, containers):
        self.pods = pods
        self.containers = containers
        if not self.pods:
            self.pods['pod'] = Pod(*containers.values())

    @property
    def pod(self):
        return self.pods['pod']

    @classmethod
    def factory(cls, path):
        containers = dict()
        pods = dict()
        spec = importlib.util.spec_from_file_location('pod', path)
        pod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pod)
        for name, value in pod.__dict__.items():
            if isinstance(value, Container):
                containers[name] = value
                value.name = name
            elif isinstance(value, Pod):
                pods[name] = value
                value.name = name

        return cls(pods, containers)
