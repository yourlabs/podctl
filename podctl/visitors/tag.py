class Tag:
    def __init__(self, tag):
        self.tag = tag

    def post_build(self, script):
        script.append(f'umounts && trap - 0 && buildah commit $ctr {self.tag}')
