from sqlalchemy import Column, Boolean, Integer, Float, String, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import UniqueConstraint
import datetime

Base = declarative_base()

class Player(Base):

    __tablename__ = 'players'
    id = Column(Integer, primary_key=True)
    type = Column(String(20))

    mlb_id = Column(String(20))
    retrosheet_id = Column(String(20))
    bp_id = Column(String(20))
    fg_id = Column(String(20))
    lahman_id = Column(String(20))
    steamer_id = Column(String(20))

    last_name = Column(String(50))
    first_name = Column(String(50))
    birthdate = Column(Date)

    __mapper_args__ = {
        'polymorphic_identity': 'players',
        'polymorphic_on': type
    }

    def age(self, from_date=datetime.date.today()):
        return (from_date - self.birthdate)

    def prettyprint(self):
        print('%s, %s (id: %d, FG ID: %s)' % \
              (self.last_name, self.first_name, self.id, self.fg_id))

    @classmethod
    def id_fields(cls):
        return ['mlb_id', 'retrosheet_id', 'bp_id', 'fg_id', 
                'lahman_id', 'steamer_id']

    @classmethod
    def name_fields(cls):
        return ['last_name', 'first_name']

class Batter(Player):

    __tablename__ = 'batters'
    id = Column(Integer, ForeignKey('players.id'), primary_key=True)
    projections = relationship('BatterProjection', backref='batter')

    __mapper_args__ = {
        'polymorphic_identity': 'batters'
    }

    def __repr__(self):
        return '<Batter %d (%s, %s)>' % (self.id, self.last_name, self.first_name)

    def prettyprint(self):
        super(Batter, self).prettyprint()
        print()
        print('%26s : %5s %5s %3s %3s %3s %3s' % \
              ('Projection', 'OBP', 'SLG', 'HR', 'R', 'RBI', 'SB'))
        for proj in self.projections:
            statline = '%20s, %4d :' % \
                       (proj.projection_system.name, proj.projection_system.year)
            statline += (' %5.3f' % proj.obp) if proj.obp is not None else ' -----'
            statline += (' %5.3f' % proj.slg) if proj.slg is not None else ' -----'
            statline += (' %3d' % proj.hr) if proj.hr is not None else ' ---'
            statline += (' %3d' % proj.r) if proj.r is not None else ' ---'
            statline += (' %3d' % proj.rbi) if proj.rbi is not None else ' ---'
            statline += (' %3d' % proj.sb) if proj.sb is not None else ' ---'
            print(statline)

class Pitcher(Player):

    __tablename__ = 'pitchers'
    id = Column(Integer, ForeignKey('players.id'), primary_key=True)
    projections = relationship('PitcherProjection', backref='pitcher')

    __mapper_args__ = {
        'polymorphic_identity': 'pitchers'
    }

    def __repr__(self):
        return '<Pitcher %d (%s, %s)>' % (self.id, self.last_name, self.first_name)

    def prettyprint(self):
        super(Pitcher, self).prettyprint()
        print()
        print('%26s : %3s %3s %5s %3s %5s %5s' % \
              ('Projection', 'W', 'SV', 'ERA', 'K', 'WHIP', 'IP'))
        for proj in self.projections:
            statline = '%20s, %4d :' % \
                       (proj.projection_system.name, proj.projection_system.year)
            statline += (' %3d' % proj.w) if proj.w is not None else ' ---'
            statline += (' %3d' % proj.sv) if proj.sv is not None else ' ---'
            statline += (' %5.2f' % proj.era) if proj.era is not None else ' -----'
            statline += (' %3d' % proj.k) if proj.k is not None else ' ---'
            statline += (' %5.3f' % proj.whip) if proj.whip is not None else ' -----'
            statline += (' %5.1f' % proj.ip) if proj.ip is not None else ' -----'
            print(statline)

class ProjectionSystem(Base):

    __tablename__ = 'projection_systems'
    id = Column(Integer, primary_key=True)

    name = Column(String(20))
    year = Column(Integer)
    is_actual = Column(Boolean)

    batter_projections = relationship('BatterProjection', backref='projection_system')
    pitcher_projections = relationship('PitcherProjection', backref='projection_system')

    __table_args__ = ( UniqueConstraint('name', 'year'), )

    def __repr__(self):
        return '<ProjectionSystem %d (%s, %d)>' % (self.id, self.name, self.year)

class BatterProjection(Base):

    __tablename__ = 'batter_projections'
    id = Column(Integer, primary_key=True)
    batter_id = Column(Integer, ForeignKey('batters.id'))
    projection_system_id = Column(Integer, ForeignKey('projection_systems.id'))
    UniqueConstraint('batter_id', 'projection_id')

    team = Column(String(3))

    pa = Column(Float)
    ab = Column(Float)
    r = Column(Float)
    rbi = Column(Float)
    h = Column(Float)
    h1b = Column(Float)
    h2b = Column(Float)
    h3b = Column(Float)
    hr = Column(Float)
    sb = Column(Float)
    cs = Column(Float)
    bb = Column(Float)
    k = Column(Float)
    hbp = Column(Float)
    sac = Column(Float)
    sf = Column(Float)
    avg = Column(Float)
    obp = Column(Float)
    slg = Column(Float)
    positions = Column(String(20))
    rookie = Column(Integer)

    def __repr__(self):
        return '<BatterProjection %d>' % (self.id)

class PitcherProjection(Base):

    __tablename__ = 'pitcher_projections'
    id = Column(Integer, primary_key=True)
    pitcher_id = Column(Integer, ForeignKey('pitchers.id'))
    projection_system_id = Column(Integer, ForeignKey('projection_systems.id'))
    UniqueConstraint('pitcher_id', 'projection_id')

    team = Column(String(3))

    w = Column(Float)
    l = Column(Float)
    sv = Column(Float)
    ip = Column(Float)
    h = Column(Float)
    r = Column(Float)
    er = Column(Float)
    ra = Column(Float)
    era = Column(Float)
    hr = Column(Float)
    bb = Column(Float)
    k = Column(Float)
    wp = Column(Float)
    hbp = Column(Float)
    whip = Column(Float)
    g = Column(Float)
    gs = Column(Float)

    rookie = Column(Integer)

    def __repr__(self):
        return '<PitcherProjection %d>' % (self.id)
