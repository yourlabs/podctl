from .build import BuildScript
from .visitable import Visitable


class Container(Visitable):
    default_scripts = dict(
        build=BuildScript,
    )
