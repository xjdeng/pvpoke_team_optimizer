
class Pokemon(object):
    
    def __init__(self, identifier, nickname = None):
        self.identifier = identifier
        if not nickname:
            nickname = identifier
        self.nickname = nickname
        self.type = identifier.split("-")[0]