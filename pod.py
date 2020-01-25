"""
Basic pod to contain the podctl command.

For advanced examples, check the examples sub-directory of the git repository.
"""
from podctl import *


podctl = Container(
    Base('docker.io/centos'),
    Packages('podman', 'buildah', 'python3'),
    User('app', 1000, '/app'),
    Copy(['setup.py', 'podctl'], '/app'),
    Pip('/app'),
    Config(cmd='podctl', author='jpic'),
    Commit('docker.io/yourlabs/podctl'),
)
