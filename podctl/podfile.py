import importlib
import os

from .container import Container
from .pod import Pod


class Podfile:
    def __init__(self, pods, containers, path, tests):
        self.pods = pods
        self.containers = containers
        self.path = path
        self.tests = tests

        if not self.pods:
            self.pods['pod'] = Pod(*containers.values())

        for pod in self.pods.values():
            for container in pod.containers:
                container.pod = pod

    @property
    def pod(self):
        return self.pods['pod']

    @classmethod
    def factory(cls, path):
        containers = dict()
        pods = dict()
        tests = dict()
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
            elif callable(value) and value.__name__.startswith('test_'):
                tests[value.__name__] = value

        return cls(pods, containers, path, tests)
