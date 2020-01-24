import os
from pathlib import Path

from pod import Pod


def test_pod_file():
    path = Path(os.path.dirname(__file__)) / '..' / 'pod.py'
    pod = Pod.factory(path)
    assert pod['podctl']
