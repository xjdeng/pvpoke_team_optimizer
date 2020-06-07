from abc import ABC
from itertools import combinations 
try:
    import EasyWebdriver
except ImportError:
    print("Missing EasyWebdriver. Please get it at: https://github.com/xjdeng/EasyWebdriver")
    raise ImportError
import time
import pandas as pd
import tempfile
import sys
from path import Path as path

SAVEFILE = "pogoqueue.csv"
RESULTFILE = "pogoresult.csv"
LEAGUEFILE = "pogoleague.txt"

defaulttemp = tempfile.gettempdir()
league_lookup = {'great': 1500, 'ultra': 2500, 'master': 10000, 1500: 1500, \
              2500: 2500, 10000: 10000, '1500': 1500, '2500': 2500, '10000': \
              10000}

class InvalidLineupException(Exception):
    pass

class TooManyRequiredPokemons(Exception):
    pass

class TimeOutError(Exception):
    pass

class InvalidLeagueException(Exception):
    pass

class Pokemon(object):
    
    def __init__(self, identifier, nickname = None):
        self.identifier = identifier.lower()
        if not nickname:
            nickname = identifier
        self.nickname = nickname
        self.type = identifier.split("-")[0]
        
    def __str__(self):
        return "Type: {}, Nickname: {}".format(self.type, self.nickname)
    
class LineupQueue(object):
    
    def __init__(self, league, folder = defaulttemp):

        self.folder = folder
        self.league = league
        self.data = pd.DataFrame(columns = ['pokemon1','pokemon2','pokemon3',\
                                            'url'])
    
    @classmethod
    def from_folder(cls, folder = defaulttemp):
        with open("{}/{}".format(folder, LEAGUEFILE),'r') as f:
            league = f.read().strip()
        res = cls(league, folder)
        res.data = pd.read_csv("{}/{}".format(folder, SAVEFILE), index_col = 0)
        return res
    
    def add(self, lineup):
        if self.league != lineup.league:
            raise InvalidLeagueException
        pokemons = list(lineup.pokemons)
        row = [pokemons[0].nickname, pokemons[1].nickname, \
               pokemons[2].nickname, lineup.make_rating_url()]
        i = len(self.data)
        self.data.loc[i] = row
        
    def save(self):
        self.data.to_csv("{}/{}".format(self.folder, SAVEFILE))
        with open("{}/{}".format(self.folder, LEAGUEFILE),'w') as f:
            f.write(str(self.league))
            
    def evaluate(self, browser = None, wait = 0.5, tries = 20):
        if browser is None:
            browser = EasyWebdriver.Chrome()
        while len(self.data.index) > 0:
            idx = self.data.index[0]
            url = self.data['url'].loc[idx]
            rating = ""
            browser.get(url)
            for i in range(0, tries):
                rating = browser.find_element_by_class_name("threat-score").text
                try:
                    intrating = int(rating)
                    break
                except ValueError:
                    pass
                time.sleep(wait)
            if rating == "":
                raise TimeOutError
            try:
                df = pd.read_csv("{}/{}".format(self.folder, RESULTFILE),\
                                 index_col = 0)
            except FileNotFoundError:
                df = pd.DataFrame(columns = ['pokemon1','pokemon2','pokemon3',\
                                            'url','rating'])
            row = list(self.data[['pokemon1','pokemon2','pokemon3']].loc[idx]) +\
            [url, intrating]
            j = len(df)
            df.loc[j] = row
            df.to_csv("{}/{}".format(self.folder, RESULTFILE))
            self.data.drop(axis=0, index=idx, inplace=True)
            self.save()
        try:
            df.to_csv(RESULTFILE)
        except IOError:
            print("Warning: could not save results file")
        return df
        
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
        
    @classmethod
    def from_csv(cls, csvfile, required1 = None, required2 = None):
        required = set([required1, required2])
        df = pd.read_csv(csvfile)
        res = cls()
        for identifier, nickname in zip(df['identifier'],df['nickname']):
            pokemon = Pokemon(identifier, nickname)
            require = False
            if (identifier in required) or (nickname in required):
                require = True
            res.add(pokemon, require)
        return res
        
    def add(self, pokemon, required = False):
        super().add(pokemon)
        if required:
            if (len(self.required) == 2) & (pokemon not in self.required):
                raise TooManyRequiredPokemons
            self.required.add(pokemon)
    
    def create_lineups(self):
        optional = self.pokemons - self.required
        k = 3 - len(self.required)
        lineups = list(combinations(optional, k))
        for i,lineup in enumerate(lineups):
            for pokemon in self.required:
                lineups[i] = list(lineups[i])
                lineups[i].append(pokemon)
        return lineups
    
    def evaluate(self, league):
        lq = LineupQueue(league)
        for l in self.create_lineups():
            try:
                lineup = Lineup(*tuple(l), league)
                lq.add(lineup)
            except InvalidLineupException:
                pass
        lq.save()
        return lq.evaluate()
        

class Lineup(PokemonCollection):
    
    def __init__(self, pokemon1, pokemon2, pokemon3, league):
        super().__init__()
        self.add(pokemon1)
        self.add(pokemon2)
        self.add(pokemon3)
        self.raise_for_validation()
        self.league = league_lookup[league]
    
    def raise_for_validation(self):
        if len(self.pokemons) != 3:
            raise InvalidLineupException
        if len(self.types) != 3:
            raise InvalidLineupException
            
    def get_rating(self, league, browser = None, wait = 0.5, tries = 20):
        if browser is None:
            browser = EasyWebdriver.Chrome()
        url = self.make_rating_url(league)
        rating = ""
        for i in range(0, tries):
            browser.get(url)
            rating = browser.find_element_by_class_name("threat-score").text
            try:
                intrating = int(rating)
                return intrating
            except ValueError:
                pass
            time.sleep(wait)
        raise TimeOutError
    
    def make_rating_url(self):
        pokemons = list(self.pokemons)
        return "https://pvpoke.com/team-builder/all/{}/{}%2C{}%2C{}".format(\
                self.league, pokemons[0].identifier, pokemons[1].identifier, \
                pokemons[2].identifier)
            
def cleanup():
    p1 = path("{}/{}".format(defaulttemp, RESULTFILE))
    p2 = path("{}/{}".format(defaulttemp, SAVEFILE))
    if p1.exists():
        p1.remove()
    if p2.exists():
        p2.remove()

if __name__ == "__main__":
    args = sys.argv
    if len(args) == 1:
        lq = LineupQueue.from_folder()
        lq.evaluate()
    elif len(args) == 2:
        lq = LineupQueue.from_folder(args[1])
        lq.evaluate()
    elif len(args) == 3:
        cleanup()
        mons = Roster.from_csv(args[1])
        league = league_lookup[args[2]]
        mons.evaluate(league)
    elif len(args) == 4:
        cleanup()
        mons = Roster.from_csv(args[1], args[3])
        league = league_lookup[args[2]]
        mons.evaluate(league)
    elif len(args) == 5:
        cleanup()
        mons = Roster.from_csv(args[1], args[3], args[4])
        league = league_lookup[args[2]]
        mons.evaluate(league)
    else:
        print("Invalid # of paramters")