class Service:
    def __init__(self, name, container, restart=None):
        self.name = name
        self.container = container
        self.restart = restart
