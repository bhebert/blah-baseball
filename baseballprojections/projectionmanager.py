from baseballprojections.helper import getSQLAlchemyFields
from baseballprojections.schema import *
from sqlalchemy import create_engine, or_, and_
from sqlalchemy.orm import sessionmaker
import csv
import datetime
import inspect
import itertools

Session = sessionmaker()

class ProjectionManager(object):

    def __init__(self, dburl='sqlite://'):
        
        self.engine = create_engine(dburl)
        Session.configure(bind=self.engine)
        self.session = Session()
        Base.metadata.create_all(self.engine)

    def add_or_update_player(self, player_type, overwrite=False, 
                             **kwargs):
        """
        Add a player to the database. If a player is already found with 
        matching ids, populate any missing fields (overwrite=False) or 
        overwrite whatever values they might have (overwrite=True). 

        If no id fields are supplied but last_name and first_name (and 
        optionally birthdate) are supplied, tries to match on that. Not ideal
        due to nicknames, name changes, players with identical names, etc. In
        this case this function will _not_ try to create a new player, but 
        will raise an exception if no players are found. 
        """

        if player_type == 'batter':
            #player_class = Batter
            player_class = Player
        elif player_type == 'pitcher':
            #player_class = Pitcher
            player_class = Player
        elif player_type == 'all':
            player_class = Player
        else:
            raise Exception('Error: add_or_update_player must be called with '\
                            'player_type = either "batter" or "pitcher" or "all"')

        matches = []

        id_clauses = [ (getattr(player_class, k) == kwargs[k])
                       for k in Player.id_fields() 
                       if (k in kwargs and kwargs[k] != '') ]
#        name_clauses = [ (getattr(player_class, k) == kwargs[k])
#                         for k in Player.name_fields()
#                         if (k in kwargs and kwargs[k] != '') ]
        
        criteria = {}
        if player_type != 'all' and len(id_clauses) > 0:
            matches = self.query(player_class).filter(or_(*id_clauses)).all()
 #           names_only = False
 #       elif len(name_clauses) > 0:
 #           matches = self.query(player_class).filter(and_(*name_clauses)).all()
 #           names_only = True
 #       elif player_type != 'all':
#            raise Exception('Error: add_or_update_player must be called with '\
#                            'at least one id parameter or both last_name and '\
#                            'first_name parameters')

        match = None

        if len(matches) > 1:
            raise Exception('Error: multiple matches found: %s' % matches)
        elif len(matches) == 1:
            match = matches[0]
            for field, value in kwargs.items():
                if overwrite or getattr(match, field) is None or getattr(match, field) == '':
                    setattr(match, field, value)
        elif len(id_clauses) > 0:
            #if names_only:
 #               raise Exception('Error: could not find player matching '\
#                                'criteria %s' % kwargs)
#            else:
            
            if player_type == 'all':
                match = player_class(**kwargs)
                self.session.merge(match)

#        self.session.commit()
        return match

    def add_or_update_projection_system(self, name, year, is_actual):
        """
        Add a projection system to the database. 
        """
        projection_system = self.query(ProjectionSystem).\
                                 filter(ProjectionSystem.name == name).\
                                 filter(ProjectionSystem.year == year).\
                                 first()
        if projection_system is None:
            projection_system = ProjectionSystem(name=name, year=year, 
                                                 is_actual=is_actual)
            self.session.add(projection_system)
#            self.session.commit()
        return projection_system

    def add_batter_projection(self, **kwargs):
        """
        Add a projection for an individual batter to the database. 
        """
        projection = BatterProjection(**kwargs)
        self.session.add(projection)
#        self.session.commit()
        return projection

    def add_pitcher_projection(self, **kwargs):
        """
        Add a projection for an individual pitcher to the database. 
        """
        projection = PitcherProjection(**kwargs)
        self.session.add(projection)
 #       self.session.commit()
        return projection

    def read_projection_csv(self, filename, projection_name, year, is_actual,
                            player_type, header_row, post_processor=None, 
                            skip_rows=1, verbose=False):

        if player_type not in ('batter', 'pitcher','all'):
            raise Exception('player_type is %s, must be either '\
                            '"batter" or "pitcher" or "all"' % player_type)

        if player_type != 'all':
            projection_system = self.add_or_update_projection_system('%s' % projection_name, 
                                                                 year, 
                                                                 is_actual)
        reader = csv.reader(open(filename, 'r'))
        for i in range(skip_rows):
            next(reader)
        n = len(header_row)

        add_player_args = getSQLAlchemyFields(Player)
        add_batter_args = getSQLAlchemyFields(Batter)
        add_pitcher_args = getSQLAlchemyFields(Pitcher)
        add_batter_projection_args = getSQLAlchemyFields(BatterProjection)
        add_pitcher_projection_args = getSQLAlchemyFields(PitcherProjection)

        count = 0

        for row in reader:

            player = None
            projection = None

            data = dict(zip(header_row, row[:n]))
            if post_processor is not None:
                data = post_processor(data)


            if player_type == 'batter':
                player_data = { x: data[x] for x in add_batter_args if x in data }
                player_data['player_type'] = 'batter'
                try:
                    player = self.add_or_update_player(**player_data)
                    if player is None:
                        if verbose or (('mlb_id' in data or 'fg_id' in data) and data['pa']>10):
                            print('Player not matched:')
                            print(player_data)
                    else:
                        projection_data = { x: data[x] for x in add_batter_projection_args
                                            if x in data }
                        projection_data['batter_id'] = player.id
                        projection_data['projection_system_id'] = projection_system.id
                        projection = self.add_batter_projection(**projection_data)
                except Exception as e:
                        print(data)
                        print(e)

            elif player_type == 'pitcher':
                player_data = { x: data[x] for x in add_pitcher_args if x in data }
                player_data['player_type'] = 'pitcher'
                try:
                    player = self.add_or_update_player(**player_data)
                    if player is None:
                        if verbose or (('mlb_id' in data or 'fg_id' in data) and data['ip']>5):
                            print('Player not matched:')
                            print(player_data)
                    else:
                        projection_data = { x: data[x] for x in add_pitcher_projection_args
                                            if x in data }
                        projection_data['pitcher_id'] = player.id
                        projection_data['projection_system_id'] = projection_system.id
                        projection = self.add_pitcher_projection(**projection_data)
                except Exception as e:
                        print(data)
                        print(e)
                        
            elif player_type == 'all':
                player_data = { x: data[x] for x in add_player_args if x in data }
                player_data['player_type'] = 'all'
                try:
                    player = self.add_or_update_player(**player_data)
                except Exception as e:
                        print(e)
                        
            if verbose and (player is not None) and (projection is not None):
                #print('%s, %s' % (player, projection))
                print('%s',player)

            count = count+1
            if count % 1000 == 0:
                print('loaded %d' % count)
                self.session.commit()
                
        self.session.commit()

    # shortcuts

    def query(self, *args):
        return self.session.query(*args)

    def rollback(self):
        return self.session.rollback()

    # next two generate an iterator { player: (player, projection) }

    def batter_projection_groups(self, filter_clause=None):

 #       q = self.query(Batter, BatterProjection).\
#                 join(BatterProjection).join(ProjectionSystem)
        q = self.query(Player, BatterProjection).\
                 join(BatterProjection).join(ProjectionSystem)
        if filter_clause is not None:
            q = q.filter(filter_clause)
        q = q.order_by(Batter.id)
        return itertools.groupby(q, lambda x: x[0])

    def pitcher_projection_groups(self, filter_clause=None):

 #       q = self.query(Pitcher, PitcherProjection).\
#                 join(PitcherProjection).join(ProjectionSystem)
        q = self.query(Player, PitcherProjection).\
                 join(PitcherProjection).join(ProjectionSystem)
        if filter_clause is not None:
            q = q.filter(filter_clause)
        q = q.order_by(Pitcher.id)
        return itertools.groupby(q, lambda x: x[0])

    # Helper functions for the Lasso code

    def get_player_year_data(self, years, systems, player_type, stats, 
                             stat_functions, includeMissing=False):

        proj_data = {}

        for stat in stats:
            stat_function = stat_functions[stat]
            proj_data[stat] = {}

            systems2 = list(filter(lambda s: not ((stat in ['sv','saverate']) and s=='zips'),systems))
            
            if stat_function is None:
                stat_function = lambda projection: getattr(projection, stat)

            for year in years:

                group_filter = and_(ProjectionSystem.year == year,
                                    ProjectionSystem.name.in_(systems2))
                if player_type == 'batter':
                    players = self.batter_projection_groups(group_filter)
                else:
                    players = self.pitcher_projection_groups(group_filter)

                for player, pair in players:
                    #print player, pair
                    key = str(player.fg_id) + "_" + str(year)
                    projs = { system: None for system in systems2 }

                    for (_, projection) in pair:
                        sys = projection.projection_system
                        if sys.name in projs:
                            projs[sys.name] = stat_function(projection)

                    if includeMissing or not any(map(lambda x: x is None, projs.values())):
                        #print "ADDING %s, %s: %s" % (player.last_name, player.first_name, projs)
                        proj_data[stat][key] = projs
                    #else:
                        #print "NOT ADDING %s, %s: %s" % (player.last_name, player.first_name, projs)

        return proj_data

    def cross_projection_csv(self, csvfile, player_type, stats, 
                             filter_clause=None, verbose=False):

        if player_type == 'batter':
            player_class = Batter
        elif player_type == 'pitcher':
            player_class = Pitcher
        else:
            raise Exception('Error: cross_projection_csv must be called with '\
                            'player_type = either "batter" or "pitcher"')

        systems = self.query(ProjectionSystem).\
                       order_by(ProjectionSystem.name, ProjectionSystem.year)
        statcols = itertools.product(stats, systems)
        statcols = ["%s_%d_%s" % (system.name, system.year, stat)
                    for stat, system in statcols]
        cols = ['last_name', 'first_name', 'mlb_id']
        cols.extend(statcols)

        if player_type == 'batter':
            players = self.batter_projection_groups(filter_clause=filter_clause)
        else:
            players = self.pitcher_projection_groups(filter_clause=filter_clause)

        with open(csvfile, 'w') as f:
            writer = csv.DictWriter(f, cols)
            writer.writeheader()
            for player, pairs in players:
                if verbose: print(player)
                row = { 'last_name': player.last_name,
                        'first_name': player.first_name,
                        'mlb_id': player.mlb_id }
                for (_, projection) in pairs:
                    system = projection.projection_system
                    for stat in stats:
                        col = "%s_%d_%s" % (system.name, system.year, stat)
                        row[col] = getattr(projection, stat)
                writer.writerow(row)
