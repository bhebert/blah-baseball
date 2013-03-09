from schema import *
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.attributes import InstrumentedAttribute
import csv
import datetime
import inspect

Session = sessionmaker()

def getSQLAlchemyFields(classname):
    attribs = classname.__dict__.iteritems()
    attribs = filter(lambda (k,v): type(v) is InstrumentedAttribute, attribs)
    return map(lambda (x,_): x, attribs)

class ProjectionManager(object):

    def __init__(self, dburl='sqlite://'):
        
        self.engine = create_engine(dburl)
        Session.configure(bind=self.engine)
        self.session = Session()
        Base.metadata.create_all(self.engine)

    def add_or_update_player(self, player_type, overwrite=False, 
                             retrosheet_id=None, mlb_id=None, bp_id=None, 
                             fangraphs_id=None, lahman_id=None,
                             last_name=None, first_name=None, birthdate=None):
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

        if player_type not in ('batter', 'pitcher'):
            raise Exception('Error: add_or_update_player must be called with '\
                            'player_type = either "batter" or "pitcher"')

        matches = []
        id_fields = ['retrosheet_id', 'mlb_id', 'bp_id', 'fangraphs_id', 
                     'lahman_id']
        ids = (retrosheet_id, mlb_id, bp_id, fangraphs_id, lahman_id)
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
            if player_type == 'batter':
                match = Batter(retrosheet_id=retrosheet_id, 
                               mlb_id=mlb_id,
                               bp_id=bp_id,
                               fangraphs_id=fangraphs_id,
                               lahman_id=lahman_id,
                               last_name=last_name,
                               first_name=first_name,
                               birthdate=birthdate)
            else:
                match = Pitcher(retrosheet_id=retrosheet_id, 
                                mlb_id=mlb_id,
                                bp_id=bp_id,
                                fangraphs_id=fangraphs_id,
                                lahman_id=lahman_id,
                                last_name=last_name,
                                first_name=first_name,
                                birthdate=birthdate)
            self.session.add(match)

        self.session.commit()
        return match

    def add_projection_system(self, name, year, is_actual):
        """
        Add a projection system to the database. 
        """
        projection_system = ProjectionSystem(name=name, year=year, 
                                             is_actual=is_actual)
        self.session.add(projection_system)
        self.session.commit()
        return projection_system

    def add_batter_projection(self, **kwargs):
        """
        Add a projection for an individual batter to the database. 
        """
        projection = BatterProjection(**kwargs)
        self.session.add(projection)
        self.session.commit()
        return projection

    def add_pitcher_projection(self, **kwargs):
        """
        Add a projection for an individual pitcher to the database. 
        """
        projection = PitcherProjection(**kwargs)
        self.session.add(projection)
        self.session.commit()
        return projection

    def find_players(self, **kwargs):
        """
        Retrieves a list of players that match the indicated criteria. 
        """
        return self.session.query(Player).filter_by(**kwargs)

    def read_projection_csv(self, filename, projection_name, year, is_actual,
                            player_type, header_row, post_processor=None, 
                            skip_rows=1, verbose=False):

        if player_type not in ('batter', 'pitcher'):
            raise Exception('player_type is %s, must be either '\
                            '"batter" or "pitcher"' % player_type)

        projection_system = self.add_projection_system(projection_name, year, 
                                                       is_actual)
        reader = csv.reader(open(filename, 'r'))
        for i in range(skip_rows):
            reader.next()
        n = len(header_row)

        add_batter_args = getSQLAlchemyFields(Batter)
        add_pitcher_args = getSQLAlchemyFields(Pitcher)
        add_batter_projection_args = getSQLAlchemyFields(BatterProjection)
        add_pitcher_projection_args = getSQLAlchemyFields(PitcherProjection)

        for row in reader:

            data = dict(zip(header_row, row[:n]))
            if post_processor is not None:
                data = post_processor(data)

            if player_type == 'batter':
                player_data = { x: data[x] for x in add_batter_args if x in data }
                player_data['player_type'] = 'batter'
                player = self.add_or_update_player(**player_data)
                projection_data = { x: data[x] for x in add_batter_projection_args
                                    if x in data }
                projection_data['batter_id'] = player.id
                projection_data['projection_system_id'] = projection_system.id
                projection = self.add_batter_projection(**projection_data)

            else:
                player_data = { x: data[x] for x in add_pitcher_args if x in data }
                player_data['player_type'] = 'pitcher'
                player = self.add_or_update_player(**player_data)
                projection_data = { x: data[x] for x in add_pitcher_projection_args
                                    if x in data }
                projection_data['pitcher_id'] = player.id
                projection_data['projection_system_id'] = projection_system.id
                projection = self.add_pitcher_projection(**projection_data)

            if verbose:
                print('%s, %s' % (player, projection))

    # shortcuts

    def query(self, *args):
        return self.session.query(*args)

    def rollback(self):
        return self.session.rollback()