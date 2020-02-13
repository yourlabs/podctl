from podctl import *

ex = Container(
    Base('docker.io/alpine'),
    Packages('bash'),
    DumbInit('sleep 55'),
    Commit('test'),
)

podctl2 = Container(
    Base('docker.io/alpine'),
    Packages('bash python-dev'),
    Commit('test2'),
)


async def test_pod_story2(pod):
    await pod.script('down')()


async def test_pod_story(pod):
    await pod.script('down')()
    await pod.script('up')()
    await pod.script('down')()
