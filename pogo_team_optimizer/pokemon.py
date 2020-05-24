from abc import ABC

class Pokemon(object):
    
    def __init__(self, identifier, nickname = None):
        self.identifier = identifier
        if not nickname:
            nickname = identifier
        self.nickname = nickname
        self.type = identifier.split("-")[0]
        
class PokemonCollection(ABC):
    
    def __init__(self):
        self.pokemons = []
        self.types = set()
    
    def add(self, pokemon):
        self.pokemons.append(pokemon)
        self.types.add(pokemon.type)

class Roster(PokemonCollection):
    
    def create_lineups(self):
        pass

class Lineup(PokemonCollection):
    
    def raise_for_validation(self):
        if len(self.pokemons) != 3:
            raise InvalidLineupException
        if len(self.types) != 3:
            raise InvalidLineupException
            
    def get_rating(self):
        pass
            
class InvalidLineupException(Exception):
    pass