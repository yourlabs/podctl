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
    await pod.script('build')('ex')
    await pod.script('up')()
    await pod.script('down')()


async def aoeutest_podctl(host):
    from podctl.console_script import console_script
    console_script.options['debug'] = 'visit'
    console_script.options['debug'] = True


    from podctl.podfile import Podfile
    pod = Podfile.factory(__file__).pod

    from podctl.proc import Proc

    #await Proc('podctl', 'down')()
    #await Proc('podctl', 'build', 'ex')()
    #await Proc('podctl', '-d=cmd,out,visit', 'up', 'ex')()
    #assert host.podman('simple-ex').is_running
    ##import time; time.sleep(5)
    #await Proc('podctl', 'down')()
    #assert 'simple-ex' not in [c.name for c in host.podman.get_containers()]
    #return

    await pod.script('down')()
    await pod.script('build')('ex')
    await pod.script('up')('ex')
    assert host.podman('ex').is_running
    await pod.script('down')()
    assert 'simple-ex' not in [c.name for c in host.podman.get_containers()]
