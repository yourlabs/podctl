

class Pod:
    def __init__(self, *services, **scripts):
        self.scripts = scripts
        self.services = {s.name: s for s in services}
