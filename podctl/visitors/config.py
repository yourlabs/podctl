class Config:
    def __init__(self, **values):
        self.values = values

    def post_build(self, script):
        for key, value in self.values.items():
            script.config(f'--{key} {value}')
