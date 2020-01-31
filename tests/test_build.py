import difflib
import os
import sys

from podctl.container import Container
from podctl.build import BuildScript
from podctl.visitors import (
    Base,
    Copy,
    Packages,
    User,
)


from unittest import mock
from podctl.visitors import packages
packages.subprocess.check_call = mock.Mock()

os.environ['CACHE_DIR'] = '/test'
os.environ['CI'] = '1'


def script_test(name, *visitors):
    result = str(Container(*visitors).script('build'))
    path = os.path.join(
        os.path.dirname(__file__),
        f'test_{name}.sh',
    )

    if not os.path.exists(path):
        with open(path, 'w+') as f:
            f.write(result)
        raise Exception(f'Fixture created test_{name}.sh')
    elif os.getenv('TEST_REWRITE') and os.path.exists(path):
        os.unlink(path)
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
    script_test(
        'build_empty',
        Base('alpine'),
    )


def test_build_packages():
    script_test(
        'build_packages',
        Base('alpine'),
        Packages('bash'),
    )


def test_build_user():
    script_test(
        'build_user',
        Base('alpine'),
        User('app', 1000, '/app'),
    )


def test_build_copy():
    script_test(
        'build_copy',
        Base('alpine'),
        Copy('/test', '/app'),
    )


'''

def test_build_files():
    result = str(BuildScript(Container(
        base='alpine',
        files=[
            Directory('/app', '0500').add('setup.py', 'podctl'),
        ]
    )))
    '''
