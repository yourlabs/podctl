from podctl.visitors.commit import Commit


def test_name_parse():
    commit = Commit('foo.ee/bar/test:y')
    assert commit.registry == 'foo.ee'
    assert commit.repo == 'bar/test'
    assert commit.tags == ['y']

    commit = Commit('foo.ee/bar/test')
    assert commit.registry == 'foo.ee'
    assert commit.repo == 'bar/test'

    commit = Commit('bar/test')
    assert commit.repo == 'bar/test'

    commit = Commit('bar/test:y')
    assert commit.repo == 'bar/test'
    assert commit.tags == ['y']
