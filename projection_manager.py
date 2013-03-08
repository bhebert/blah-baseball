from schema import *
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import csv
import datetime
import inspect

Session = sessionmaker()

class ProjectionManager(object):

    def __init__(self, dburl='sqlite://'):
        
        self.engine = create_engine(dburl)
        Session.configure(bind=self.engine)
        self.session = Session()
        Base.metadata.create_all(self.engine)

    def add_or_update_player(self, type, overwrite=False, retrosheet_id=None, 
                             mlb_id=None, pecota_id=None, fangraphs_id=None, 
                             br_id=None, last_name=None, first_name=None, 
                             birthdate=None):
        """
        Add a player to the database. If a player is already found with 
        matching ids, populate any missing non-id fields (overwrite=False) or 
        overwrite them (overwrite=True). Never overwrites an id field; raises 
        an exception if inconsistent ids found. 

        If no id fields are supplied but last_name and first_name (and 
        optionally birthdate) are supplied, tries to match on that. Not ideal
        due to nicknames, name changes, players with identical names, etc. If
        there is not exactly one match, raises an exception. 
        """

        if type not in ('batter', 'pitcher'):
            raise Exception('Error: add_or_update_player must be called with '\
                            'type = either "batter" or "pitcher"')

        matches = []
        id_fields = ['retrosheet_id', 'mlb_id', 'pecota_id', 'fangraphs_id', 'br_id']
        ids = (retrosheet_id, mlb_id, pecota_id, fangraphs_id, br_id)
        name_fields = ('last_name', 'first_name')
        names = (last_name, first_name)

        criteria = {}
        if any(map(lambda x: x != None, ids)):
            criteria = { x[0]: x[1] for x in zip(id_fields, ids) 
                         if x[1] is not None }
            matches = self.find_players(**criteria).all()
        elif all(map(lambda x: x != None, name_fields)):
            criteria = { x[0]: x[1] for x in zip(name_fields, names) 
                         if x[1] is not None }
            matches = self.find_players(**criteria).all()
        else:
            raise Exception('Error: add_or_update_player must be called with '\
                            'at least one id parameter or last_name/first_name '\
                            'parameters')
 
        non_id_fields = ['last_name', 'first_name', 'birthdate']
        non_ids = [last_name, first_name, birthdate]

        if len(matches) > 1:
            raise Exception('Error: multiple matches found for criteria %s:\n '\
                            '%s' % (ids, criteria))
        elif len(matches) == 1:
            match = matches[0]
            for field, value in zip(non_id_fields, non_ids):
                if overwrite or getattr(match, field) is None:
                    setattr(match, field, value)
        else:
            if type == 'batter':
                match = Batter(retrosheet_id=retrosheet_id, 
                               mlb_id=mlb_id,
                               pecota_id=pecota_id,
                               fangraphs_id=fangraphs_id,
                               br_id=br_id,
                               last_name=last_name,
                               first_name=first_name,
                               birthdate=birthdate)
            else:
                match = Pitcher(retrosheet_id=retrosheet_id, 
                                mlb_id=mlb_id,
                                pecota_id=pecota_id,
                                fangraphs_id=fangraphs_id,
                                br_id=br_id,
                                last_name=last_name,
                                first_name=first_name,
                                birthdate=birthdate)
            self.session.add(match)

        self.session.commit()
        return match

    def add_or_update_batter(self, overwrite=False, retrosheet_id=None, 
                             mlb_id=None, pecota_id=None, fangraphs_id=None, 
                             br_id=None, last_name=None, first_name=None, 
                             birthdate=None):
        """
        Add a batter to the database. If a batter is already found with 
        matching ids, populate any missing non-id fields (overwrite=False) or 
        overwrite them (overwrite=True). Never overwrites an id field; raises 
        an exception if inconsistent ids found. 

        If no id fields are supplied but last_name and first_name (and 
        optionally birthdate) are supplied, tries to match on that. Not ideal
        due to nicknames, name changes, players with identical names, etc. If
        there is not exactly one match, raises an exception. 
        """
        return self.add_or_update_player(self, type='batter', 
                                         overwrite=overwrite,
                                         retrosheet_id=retrosheet_id,
                                         mlb_id=mlb_id,
                                         pecota_id=pecota_id,
                                         fangraphs_id=fangraphs_id,
                                         br_id=br_id,
                                         last_name=last_name,
                                         first_name=first_name,
                                         birthdate=birthdate)

    def add_or_update_pitcher(self, retrosheet_id=None, mlb_id=None, pecota_id=None, 
                    fangraphs_id=None, br_id=None, last_name=None, 
                    first_name=None, birthdate=None):
        """
        Add a pitcher to the database. If a pitcher is already found with 
        matching ids, populate any missing non-id fields (overwrite=False) or 
        overwrite them (overwrite=True). Never overwrites an id field; raises 
        an exception if inconsistent ids found. 

        If no id fields are supplied but last_name and first_name (and 
        optionally birthdate) are supplied, tries to match on that. Not ideal
        due to nicknames, name changes, players with identical names, etc. If
        there is not exactly one match, raises an exception. 
        """
        return self.add_or_update_player(self, type='pitcher', 
                                         overwrite=overwrite,
                                         retrosheet_id=retrosheet_id,
                                         mlb_id=mlb_id,
                                         pecota_id=pecota_id,
                                         fangraphs_id=fangraphs_id,
                                         br_id=br_id,
                                         last_name=last_name,
                                         first_name=first_name,
                                         birthdate=birthdate)

    def add_projection_system(self, name, year):
        """
        Add a projection system to the database. 
        """
        projection_system = ProjectionSystem(name=name, year=year)
        self.session.add(projection_system)
        self.session.commit()
        return projection_system

    def add_batter_projection(self, batter_id=None, projection_system_id=None,
                              team=None, pa=None, ab=None, r=None, rbi=None,
                              h=None, h2b=None, h3b=None, hr=None, sb=None,
                              cs=None, bb=None, k=None, hbp=None, sac=None,
                              sf=None):
        """
        Add a projection for an individual batter to the database. 
        """
        projection = BatterProjection(batter_id=batter_id, 
                                      projection_system_id=projection_system_id,
                                      team=team,
                                      pa=pa,
                                      ab=ab,
                                      r=r,
                                      rbi=rbi,
                                      h=h,
                                      h2b=h2b,
                                      h3b=h3b,
                                      hr=hr,
                                      sb=sb,
                                      cs=cs,
                                      bb=bb,
                                      k=k,
                                      hbp=hbp,
                                      sac=sac,
                                      sf=sf)
        self.session.add(projection)
        self.session.commit()
        return projection

    def add_pitcher_projection(self, pitcher_id=None, projection_id=None,
                               team=None, w=None, l=None, ip=None, h=None,
                               r=None, er=None, hr=None, bb=None, k=None,
                               wp=None, hbp=None):
        """
        Add a projection for an individual pitcher to the database. 
        """
        projection = PitcherProjection(pitcher_id=batter_id, 
                                       projection_id=projection_id,
                                       team=team,
                                       w=w,
                                       l=l,
                                       ip=ip,
                                       h=h,
                                       r=r,
                                       er=er,
                                       hr=hr,
                                       bb=bb,
                                       k=k,
                                       wp=wp,
                                       hbp=hbp)
        self.session.add(projection)
        self.session.commit()
        return projection

    def find_players(self, **kwargs):
        """
        Retrieves a list of players that match the indicated criteria. 
        """
        return self.session.query(Player).filter_by(**kwargs)

    def read_projection_csv(self, filename, projection_name, year, player_type,
                            header_row, calculated_key={}, skip_rows=1, 
                            verbose=False):

        if player_type not in ('batter', 'pitcher'):
            raise Exception('player_type is %s, must be either '\
                            '"batter" or "pitcher"' % player_type)

        projection_system = self.add_projection_system(projection_name, year)
        reader = csv.reader(open(filename, 'r'))
        for i in range(skip_rows):
            reader.next()
        n = len(header_row)

        add_batter_args = inspect.getargspec(self.add_or_update_batter).args
        add_pitcher_args = inspect.getargspec(self.add_or_update_pitcher).args
        add_batter_projection_args = inspect.getargspec(self.add_batter_projection).args
        add_pitcher_projection_args = inspect.getargspec(self.add_pitcher_projection).args

        for row in reader:

            data = dict(zip(header_row, row[:n]))
            for k in calculated_key:
                data[k] = calculated_key[k](data)

            if player_type == 'batter':
                player_data = { x: data[x] for x in add_batter_args if x in data }
                player = self.add_or_update_batter(**player_data)
                projection_data = { x: data[x] for x in add_batter_projection_args
                                    if x in data }
                projection_data['batter_id'] = player.id
                projection_data['projection_system_id'] = projection_system.id
                projection = self.add_batter_projection(**projection_data)
                if verbose:
                    print('%s, %s' % (player, projection))

            else:
                player_data = { x: data[x] for x in add_pitcher_args if x in data }
                player = self.add_or_update_pitcher(**player_data)
                projection_data = { x: data[x] for x in add_pitcher_projection_args
                                    if x in data }
                projection_data['pitcher_id'] = player.id
                projection_data['projection_system_id'] = projection_system.id
                projection = self.add_pitcher_projection(**projection_data)

            if verbose:
                print('%s, %s' % (player, projection))

    # PECOTA readers

    def read_pecota_batters_2011(self, filename, verbose=False):

        header_row = ['mlb_id', '', 'last_name', 'first_name', 'team', '', '', 
                      '', '', '', '', 'birthdate', '', 'pa', 'ab', 'r', 'h1b', 
                      'h2b', 'h3b', 'hr', 'rbi', 'bb', 'hbp', 'k', 'sb', 'cs', 
                      'sac', 'sf']

        calculated_key = {
            'birthdate': lambda x: datetime.datetime.strptime(x['birthdate'], '%m/%d/%Y'),
            'h': lambda x: sum(map(int, [x['h1b'], x['h2b'], x['h3b'], x['hr']])),
        }
        self.read_projection_csv(filename, 'pecota', 2011, 'batter',
                                 header_row, calculated_key,
                                 verbose=verbose)

    def read_pecota_batters_2012(self, filename, verbose=False):

        header_row = ['mlb_id', 'bp_id', 'last_name', 'first_name', '', '', '',
                      '', '', '', 'team', '', '', '', 'pa', 'ab', 'r', 'h1b', 
                      'h2b', 'h3b', 'hr', 'h', '', 'rbi', 'bb', 'hbp', 'k', 
                      'sac', 'sf', '', 'sb', 'cs']
        calculated_key = {}
        self.read_projection_csv(filename, 'pecota', 2012, 'batter',
                                 header_row, calculated_key,
                                 verbose=verbose)

    def read_pecota_batters_2013(self, filename, verbose=False):

        header_row = ['mlb_id', '', 'bp_id', 'last_name', 'first_name', '', '', 
                      '', '', '', '', 'team', '', '', '', 'pa', 'ab', 'r', 
                      'h1b', 'h2b', 'h3b', 'hr', 'h', '', 'rbi', 'bb', 'hbp', 
                      'k', 'sac', 'sf', '', 'sb', 'cs']
        calculated_key = {}
        self.read_projection_csv(filename, 'pecota', 2013, 'batter',
                                 header_row, calculated_key,
                                 verbose=verbose)

    # ZIPS readers

    def read_zips_batters_2011(self, filename, verbose=False):

        header_row = ['mlb_id', '', 'last_name', 'first_name', 'team', '', '', 
                      '', '', '', 'avg', 'obp', 'slg', '', 'ab', 'r', 'h', 
                      'h2b', 'h3b', 'hr', 'rbi', 'bb', 'k', 'hbp', 'sb', 'cs', 
                      'sac', 'sf', '', '', '', 'pa']

        calculated_key = {}
        self.read_projection_csv(filename, 'zips', 2011, 'batter',
                                 header_row, calculated_key,
                                 verbose=verbose)

    def read_zips_batters_2012(self, filename, verbose=False):

        header_row = ['mlb_id', 'full_name', 'team', '', '', '', 'avg', 'obp', 
                      'slg', '', 'ab', 'r', 'h', 'h2b', 'h3b', 'hr', 'rbi', 
                      'bb', 'k', 'hbp', 'sb', 'cs', 'sac', 'sf', '', '', '', 'pa']

        calculated_key = {
            'last_name': last_name_from_full_name,
            'first_name': first_name_from_full_name,
        }
        self.read_projection_csv(filename, 'zips', 2012, 'batter',
                                 header_row, calculated_key,
                                 verbose=verbose)

    def read_zips_batters_2013(self, filename, verbose=False):

        header_row = ['mlb_id', 'full_name', 'team', '', '', '', 'avg', 'obp', 
                      'slg', '', 'pa', 'ab', 'r', 'h', 'h2b', 'h3b', 'hr', 
                      'rbi', 'bb', 'k', 'hbp', 'sb', 'cs', 'sac', 'sf']

        calculated_key = {
            'last_name': last_name_from_full_name,
            'first_name': first_name_from_full_name,
        }
        self.read_projection_csv(filename, 'zips', 2013, 'batter',
                                 header_row, calculated_key,
                                 verbose=verbose)

    # Steamer readers

    def read_steamer_batters_2011(self, filename, verbose=False):

        header_row = ['mlb_id', 'full_name', '', 'team', '', '', '', '', '', 
                      '', 'bb', 'hbp', 'sac', 'sf', 'ab', 'k', '', 'h', 'h1b', 
                      'h2b', 'h3b', 'hr', '', 'sb', 'cs', 'avg', 'obp', 
                      'slg', 'ops', '', 'r', 'rbi', 'pa']

        calculated_key = {
            'last_name': last_name_from_full_name,
            'first_name': first_name_from_full_name,
        }
        self.read_projection_csv(filename, 'steamer', 2011, 'batter',
                                 header_row, calculated_key,
                                 verbose=verbose)

    def read_steamer_batters_2012(self, filename, verbose=False):

        header_row = ['mlb_id', 'full_name', '', '', '', '', '', 'team', '', 
                      '', '', 'pa', 'ab', 'bb', 'hbp', 'sac', 'sf', 'k', '', 
                      'h', 'h3b', 'h2b', 'h1b', 'hr', 'r', 'rbi', 'sb', 'cs',
                      'avg', 'obp', 'slg']

        calculated_key = {
            'last_name': last_name_from_full_name,
            'first_name': first_name_from_full_name,
        }
        self.read_projection_csv(filename, 'steamer', 2012, 'batter',
                                 header_row, calculated_key,
                                 verbose=verbose)

    def read_steamer_batters_2013(self, filename, verbose=False):

        header_row = ['mlb_id', 'first_name', 'last_name', '', '', '', 'team', 
                      'pa', '', '', 'bb', 'k', 'hbp', '', 'sac', 'sf', 'ab', 
                      'h', 'h1b', 'h2b', 'h3b', 'hr', 'avg', 'obp', 'slg', 
                      'sb', 'cs', 'r', 'rbi']

        calculated_key = {}
        self.read_projection_csv(filename, 'steamer', 2013, 'batter',
                                 header_row, calculated_key,
                                 verbose=verbose)

# Helper functions

def split_full_name(full_name, sep=' '):
    return full_name.split(sep)

def first_name_from_full_name(full_name, sep=' '):
    split_result = split_full_name(full_name, sep=sep)
    if len(split_result) == 0: return None
    else: return split_result[0]

def last_name_from_full_name(full_name, sep=' '):
    split_result = split_full_name(full_name, sep=sep)
    if len(split_result) < 1: return None
    else: return split_result[1]