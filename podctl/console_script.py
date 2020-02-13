'''
docker & docker-compose frustrated me, podctl unfrustrates me.
'''

import asyncio
import cli2
import inspect
import os
import sys

from .container import Container
from .exceptions import Mistake, WrongResult
from .pod import Pod
from .podfile import Podfile
from .proc import output
from .service import Service


@cli2.option('debug', alias='d', help='Display debug output.')
async def test(*args, **kwargs):
    """Run podctl test over a bunch of paths."""
    report = []
    try:
      columns = os.get_terminal_size(0)[0]
    except:
      columns = 80
    for arg in args:
        candidates = [
            os.path.join(os.getcwd(), arg, 'pod.py'),
            os.path.join(os.getcwd(), arg, 'pod_test.py'),
        ]
        for candidate in candidates:
            if not os.path.exists(candidate):
                continue
            podfile = Podfile.factory(candidate)

            # disable push
            for name, container in podfile.containers.items():
                commit = container.visitor('commit')
                if commit:
                    commit.push = False

            output.print(
                '\n\x1b[1;38;5;160;48;5;118m  BUILD START \x1b[0m'
                + ' ' + podfile.path + '\n'
            )

            old_exit_code = console_script.exit_code
            console_script.exit_code = 0
            try:
                await podfile.pod.script('build')()
            except Exception as e:
                report.append(('build ' + candidate, False))
                continue

            if console_script.exit_code != 0:
                report.append(('build ' + candidate, False))
                continue
            console_script.exit_code = old_exit_code

            for name, test in podfile.tests.items():
                name = '::'.join([podfile.path, name])
                output.print(
                        "\x1b[1;38;5;15m--> [TEST START]   "
                        + "\x1b[0m\x1b[1;38;5;226m    [" 
                        + name 
                        + "] "
                        + "#" * (int(columns) - (26 + len(name)))
                        + "\x1b[0m\n"
                )

                try:
                    await test(podfile.pod)
                except Exception as e:
                    report.append((name, False))
                    output.print(
                            "\x1b[1;38;5;15;48;5;196m[x] TEST FAIL  "
                            + "\x1b[1;38;5;196;48;5;15m   [" 
                            + name 
                            + "] "
                            + " " * (int(columns) - (21 + len(name)))
                            + "\x1b[0m\n"
                    )
                else:
                    report.append((name, True))
                    output.print(
                            "\x1b[1;38;5;10m[√] [TEST SUCCESS]  "
                            + "\x1b[0m\x1b[1;38;5;82m   [" 
                            + name 
                            + "] "
                            + "-" * (int(columns) - (26 + len(name)))
                            + "\x1b[0m\n"
                    )
                output.print('\n')

    print('\n')

    for name, success in report:
        if success:
            output.print(
                    "\x1b[1;38;5;10m  [TEST SUCCESS]  "
                    + "\x1b[0m\x1b[1;38;5;10m  [" 
                    + name 
                    + "] "
                    + "-" * (int(columns) - (23 + len(name)))
                    + "\x1b[0m\n"
            )
        else:
            output.print(
                    "\x1b[1;38;5;15;48;5;196m  [TEST FAIL]    "
                    + "\x1b[1;38;5;196;48;5;15m   [" 
                    + name 
                    + "] "
                    + " " * (int(columns) - ( 23 + len(name)))
                    + "\x1b[0m\n"
            )

    print("\n\nSummary:")
    print('########')

    success = [*filter(lambda i: i[1], report)]
    failures = [*filter(lambda i: not i[1], report)]

    output.print(
        '\n\x1b[1;38;5;200m TEST TOTAL:    \x1b[0m '
        + str(len(report))
    )
    if success:
        output.print(
            '\n\x1b[1;38;5;10m TEST SUCCESS:  \x1b[0m '
            + str(len(success))
            + "\n"
        )
    if failures:
        output.print(
            '\x1b[1;38;5;196m TEST FAIL:      \x1b[0m'
            + str(len(failures))
            + "\n"
        )

    if failures:
        console_script.exit_code = 1


class ConsoleScript(cli2.ConsoleScript):
    class Parser(cli2.Parser):
        def parse(self):
            super().parse()
            if str(self.command) == 'help':
                return

            self.forward_args = []

            found_dash = False
            for arg in self.argv:
                if arg == '--':
                    found_dash = True
                if not found_dash:
                    continue
                self.forward_args.append(arg)

            self.funckwargs['cmd'] = self.forward_args

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.options = dict()

    def __call__(self, *args, **kwargs):
        podfile = os.getenv('PODFILE', 'pod.py')
        if os.path.exists(podfile):
            self.podfile = Podfile.factory(podfile)
            for name, script in self.podfile.pod.scripts.items():
                cb = self.podfile.pod.script(name)
                cb.__doc__ = inspect.getdoc(script) or script.doc
                self[name] = cli2.Callable(
                    name,
                    cb,
                    options={o.name: o for o in script.options},
                    color=getattr(script, 'color', cli2.YELLOW),
                )
        return super().__call__(*args, **kwargs)

    def call(self, command):
        self.options = self.parser.options

        try:
            return super().call(command)
        except Mistake as e:
            print(e)
            self.exit_code = 1
        except WrongResult as e:
            print(e)
            self.exit_code = e.proc.rc


console_script = ConsoleScript(__doc__).add_module('podctl.console_script')
