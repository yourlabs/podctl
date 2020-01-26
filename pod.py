"""
Basic pod to contain the podctl command.

For advanced examples, check the examples sub-directory of the git repository.
"""
from podctl import *


podctl = Container(
    Base('quay.io/podman/stable'),
    Packages('python38', 'buildah', 'unzip', mgr='dnf'),
    Run('''
    curl -o setuptools.zip https://files.pythonhosted.org/packages/42/3e/2464120172859e5d103e5500315fb5555b1e908c0dacc73d80d35a9480ca/setuptools-45.1.0.zip
    unzip setuptools.zip
    mkdir -p /usr/local/lib/python3.8/site-packages/
    sh -c "cd setuptools-* && python3.8 setup.py install"
    easy_install-3.8 pip
    '''),
    Copy(['setup.py', 'podctl'], '/app'),
    Pip('/app', pip='pip3.8'),
    Config(cmd='podctl', author='jpic'),
    Commit('docker.io/yourlabs/podctl'),
)
