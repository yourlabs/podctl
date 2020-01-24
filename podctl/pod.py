import collections
import importlib.util


class Pod(collections.UserDict):
    @classmethod
    def factory(cls, path):
        spec = importlib.util.spec_from_file_location('pod', path)
        pod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pod)
        return pod.pod
