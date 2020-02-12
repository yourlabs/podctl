class PodctlException(Exception):
    pass


class Mistake(PodctlException):
    pass


class WrongResult(PodctlException):
    pass
