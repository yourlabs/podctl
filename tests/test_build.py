import difflib
import os
import sys

from podctl.container import Container
from podctl.build import BuildScript


def script_test(name, result):
    path = os.path.join(
        os.path.dirname(__file__),
        f'test_{name}.sh',
    )

    if not os.path.exists(path):
        with open(path, 'w+') as f:
            f.write(result)
        raise Exception('Fixture created test_build_packages.sh')
    with open(path, 'r') as f:
        expected = f.read()
    result = difflib.unified_diff(
        expected,
        result,
        fromfile='expected',
        tofile='result'
    )
    assert not list(result), sys.stdout.writelines(result)


def test_build_empty():
    result = str(BuildScript(Container()))
    script_test('build_empty', result)


def test_build_packages():
    result = str(BuildScript(Container(
        base='alpine',
        packages=['bash'],
    )))
    script_test('build_packages', result)
