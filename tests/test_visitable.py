from unittest.mock import MagicMock

from podctl.script import Script
from podctl.visitable import Visitable


class Visitor0:
    def __init__(self, name=None):
        self.name = name or 'visit0'


class Visitor1:
    def pre_build(self, script):
        script.append('pre_build')
    def build(self, script):
        script.append('build')
    def post_build(self, script):
        script.append('post_build')


def test_visitable_visitor():
    visitable = Visitable(Visitor0(), Visitor1(), build=Script())
    script = visitable.script('build')
    assert 'pre_build' in script
    assert 'build' in script
    assert 'post_build' in script


def test_visitable_visitor():
    x = Visitor0()
    assert Visitable(x).visitor('visitor0') is x


def test_visitable_variable():
    assert Visitable(Visitor0('foo')).variable('name') == 'foo'

#
#
#def test_visitable_configuration():
#    '''Attributes should be passable to constructor or as class attributes'''
#    assert Container(a='b')['a'] == 'b'
#    class Test(Container):
#        cfg = dict(a='b')
#    assert Test()['a'] == 'b'
#
#
#def test_switch_simple():
#    assert Container(a=switch(default='expected'))['a'] == 'expected'
#    assert Container(a=switch(noise='noise'))['a'] == None
#    fixture = Container(
#        'test',
#        a=switch(default='noise', test='expected')
#    )
#    assert fixture['a'] == 'expected'
#    assert [*fixture.values()][0] == 'expected'
#    assert [*fixture.items()][0][1] == 'expected'
#
#
#def test_switch_iterable():
#    class TContainer(Container):
#        cfg = dict(
#            a=switch(dev='test')
#        )
#    assert TContainer()['a'] is None
#    assert TContainer('dev')['a'] == 'test'
#    assert TContainer('dev', a=[switch(dev='y')])['a'] == ['y']
#    assert TContainer('dev', a=[switch(default='y')])['a'] == ['y']
#
#
#def test_switch_value_list():
#    assert Container('test').switch_value(
#        [switch(default='noise', test=False)]
#    ) == [False]
#
#    assert Container('none').switch_value(
#        [switch(noise='noise')]
#    ) == []
#
#
#def test_switch_value_dict():
#    assert Container('foo').switch_value(
#        dict(i=switch(default='expected', noise='noise'))
#    ) == dict(i='expected')
#
#    assert Container('test').switch_value(
#        dict(i=switch(default='noise', test='expected'))
#    ) == dict(i='expected')
#
#    assert Container('none').switch_value(
#        dict(i=switch(noise='noise'), j=dict(e=switch(none=1)))
#    ) == dict(j=dict(e=1))
