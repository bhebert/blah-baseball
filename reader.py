from schema import *
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import csv

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

    def add_batter(self, retrosheet_id=None, mlb_id=None, pecota_id=None, 
                   fangraphs_id=None, br_id=None, last_name=None, 
                   first_name=None, birthdate=None):

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
        self.session.add(ProjectionSystem(name=name, year=year))
        self.session.commit()

    def read_pecota(self, filename):
        pass
        #reader = csv.reader(open(filename, 'r'))
        #for row in reader:
        #    (mlbid, _, last_name, first_name, team, _, _, _, _, _, _, 
        #     birthdate, _, pa, ab, r, _ h2b, h3b, hr, rbi, bb, hbp, k, sb, cs,
        #     sac, sf) = row[:28]
        #f.close()