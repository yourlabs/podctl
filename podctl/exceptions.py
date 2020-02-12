class PodctlException(Exception):
    pass


class Mistake(PodctlException):
    pass


class WrongResult(PodctlException):
    def __init__(self, proc):
        self.proc = proc
        super().__init__('\n'.join([i for i in [
            f'Command failed ! Exit with {proc.rc}'
            '+ ' + proc.cmd,
            proc.out,
            proc.err,
        ]]))
