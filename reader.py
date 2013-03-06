from schema import *
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import csv
import datetime
import inspect

Session = sessionmaker()

class ProjectionReader(object):

    def __init__(self, dburl='sqlite://'):
        
        self.engine = create_engine(dburl)
        Session.configure(bind=self.engine)
        self.session = Session()
        Base.metadata.create_all(self.engine)

    def add_batter(self, retrosheet_id=None, mlb_id=None, pecota_id=None, 
                   fangraphs_id=None, br_id=None, last_name=None, 
                   first_name=None, birthdate=None):
        """
        Add a batter to the database. 
        """
        ids = (retrosheet_id, mlb_id, pecota_id, fangraphs_id, br_id)
        if not any(map(lambda x: x != None, ids)):
            raise Exception('Error: add_batter must be called with at least '\
                            'one id parameter')
        self.session.add(Batter(retrosheet_id=retrosheet_id, 
                                mlb_id=mlb_id,
                                pecota_id=pecota_id,
                                fangraphs_id=fangraphs_id,
                                br_id=br_id,
                                last_name=last_name,
                                first_name=first_name,
                                birthdate=birthdate))
        self.session.commit()

    def add_pitcher(self, retrosheet_id=None, mlb_id=None, pecota_id=None, 
                    fangraphs_id=None, br_id=None, last_name=None, 
                    first_name=None, birthdate=None):
        """
        Add a pitcher to the database. 
        """
        ids = (retrosheet_id, mlb_id, pecota_id, fangraphs_id, br_id)
        if not any(map(lambda x: x != None, ids)):
            raise Exception('Error: add_pitcher must be called with at least '\
                            'one id parameter')
        self.session.add(Pitcher(retrosheet_id=retrosheet_id, 
                                 mlb_id=mlb_id,
                                 pecota_id=pecota_id,
                                 fangraphs_id=fangraphs_id,
                                 br_id=br_id,
                                 last_name=last_name,
                                 first_name=first_name,
                                 birthdate=birthdate))
        self.session.commit()

    def add_projection_system(self, name, year):
        """
        Add a projection system to the database. 
        """
        self.session.add(ProjectionSystem(name=name, year=year))
        self.session.commit()

    def add_batter_projection(self, batter_id=None, projection_id=None,
                              team=None, pa=None, ab=None, r=None, rbi=None,
                              h=None, h2b=None, h3b=None, hr=None, sb=None,
                              cs=None, bb=None, k=None, hbp=None, sac=None,
                              sf=None):
        """
        Add a projection system for an individual batter to the database. 
        """
        self.session.add(BatterProjection(batter_id=batter_id, 
                                          projection_id=projection_id,
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
                                          sf=sf))
        self.session.commit()

    def add_pitcher_projection(self, pitcher_id=None, projection_id=None,
                               team=None, w=None, l=None, ip=None, h=None,
                               r=None, er=None, hr=None, bb=None, k=None,
                               wp=None, hbp=None):
        """
        Add a projection system for an individual pitcher to the database. 
        """
        self.session.add(PitcherProjection(pitcher_id=batter_id, 
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
                                           hbp=hbp))
        self.session.commit()

    def find_player(self, **args):
        """
        Retrieves all players that match the indicated query. 
        """
        self.session.query(Player).filter_by(**args)

    def read_projection_csv(self, filename, projection_name, year, player_type,
                            header_row, transform_data={}, skip_rows=1, 
                            verbose=False):

        if player_type not in ('batter', 'pitcher'):
            raise Exception('player_type is %s, must be either '\
                            '"batter" or "pitcher"' % player_type)
        # add check that header_row is OK

        self.add_projection_system(projection_name, year)
        reader = csv.reader(open(filename, 'r'))
        for i in range(skip_rows):
            reader.next()
        n = len(header_row)

        add_batter_args = inspect.getargspec(self.add_batter).args
        add_pitcher_args = inspect.getargspec(self.add_pitcher).args

        for row in reader:
            data_zip = zip(header_row, row[:n])
            if player_type == 'batter':
                data = filter(lambda x: x[0] in add_batter_args, data_zip)
                data = [(k, transform_data[k](v)) if k in transform_data
                        else (k, v)
                        for (k, v) in data]
                data = dict(data)
                self.add_batter(**data)
            else:
                data = dict(filter(lambda x: x[0] in add_pitcher_args,
                                   data_zip))
                self.add_pitcher(**data)
            if verbose:
                print(data)

    def read_pecota_batters_2011(self, filename, verbose=False):

        header_row = ['mlb_id', '_', 'last_name', 'first_name', 'team', '_', 
                      '_', '_', '_', '_', '_', 'birthdate', '_', 'pa', 'ab', 
                      'r', '_', 'h2b', 'h3b', 'hr', 'rbi', 'bb', 'hbp', 'k', 
                      'sb', 'cs', 'sac', 'sf']
        transform_data = {
            'birthdate': lambda x: datetime.datetime.strptime(x, '%m/%d/%Y')
        }
        self.read_projection_csv(filename, 'pecota', 2011, 'batter',
                                 header_row, transform_data,
                                 verbose=verbose)
