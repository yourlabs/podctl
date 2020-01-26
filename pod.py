"""
Basic pod to contain the podctl command.

For advanced examples, check the examples sub-directory of the git repository.
"""
from podctl import *


podctl = Container(
    Base('quay.io/podman/stable'),
    Packages('python3', 'buildah', mgr='dnf'),
    Copy(['setup.py', 'podctl'], '/app'),
    Pip('/app'),
    Config(cmd='podctl', author='jpic'),
    Commit('docker.io/yourlabs/podctl'),
)
