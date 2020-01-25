import os

from podctl import *


class Django(Container):
    tag = 'yourlabs/crudlfap'
    base = 'alpine'
    packages = [
        'bash',
        'python3',
        switch(dev='vim'),
    ]
    env = dict(FOO='bar')
    annotations = dict(test='foo')
    labels = dict(foo='test')
    cmd = 'bash'
    entrypoint = ['bash', '-v']
    ports = [1234]
    user = dict(
        shell='/bin/bash',
        name='app',
        home='/app',
        id=os.getenv('SUDO_ID', os.getenv('UID')),
    )
    volumes = [
        '/bydir',
        'byname:/byname',
        switch(dev='.:/app'),
    ]
    build = [
        'sudo pip3 install --upgrade pip',
        'pip3 install --user -e /app',
    ]
    workdir = '/app'

django = Container(
    Base('alpine'),
    Packages('bash', switch(dev='vim')),
    User(
        uid=1000,
        home='/app',
        directories=('log', 'spooler', 'static')
    ),
    switch(default=Mount('.', '/app'), production=Copy('.', '/app')),
    Npm('build'),
    Env('PATH', 'PATH=/app/node_modules/.bin:$PATH'),
    Pip('requirements.txt'),
    Env('PATH', 'PATH=$HOME/.local/bin:$PATH'),
    switch(dev=Run('''
        manage.py collectstatic --noinput --clear
        find frontend/static/dist/css -type f | xargs gzip -f -k -9
        find frontend/static/dist/js -type f | xargs gzip -f -k -9
    ''')),
    Expose(8000),
    Tag('equisafe'),
)

pod = Pod(
    Service('django', django, restart='unless-stopped'),
    Service('db',
        Container(Tag('postgresql:latest')),
        restart='unless-stopped'
    ),
)
