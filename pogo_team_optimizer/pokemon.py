from abc import ABC

class Pokemon(object):
    
    def __init__(self, identifier, nickname = None):
        self.identifier = identifier
        if not nickname:
            nickname = identifier
        self.nickname = nickname
        self.type = identifier.split("-")[0]
        
    def __str__(self):
        return "Type: {}, Nickname: {}".format(self.type, self.nickname)
        
class PokemonCollection(ABC):
    
    def __init__(self):
        self.pokemons = set()
        self.types = set()

    
    def add(self, pokemon):
        self.pokemons.add(pokemon)
        self.types.add(pokemon.type)

class Roster(PokemonCollection):
    
    def __init__(self):
        super().__init__()
        self.required = set()
        
    def add(self, pokemon, required = False):
        super().add(pokemon)
        if required:
            if (len(self.required) == 2) & (pokemon not in self.required):
                raise TooManyRequiredPokemons
            self.required.add(pokemon)
    
    def create_lineups(self):
        pass

class Lineup(PokemonCollection):
    
    def __init__(self, pokemon1, pokemon2, pokemon3):
        super().__init__()
        self.add(pokemon1)
        self.add(pokemon2)
        self.add(pokemon3)
        self.raise_for_validation()
    
    def raise_for_validation(self):
        if len(self.pokemons) != 3:
            raise InvalidLineupException
        if len(self.types) != 3:
            raise InvalidLineupException
            
    def get_rating(self, browser = None):
        pass
            
class InvalidLineupException(Exception):
    pass

class TooManyRequiredPokemons(Exception):
    pass