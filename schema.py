from sqlalchemy import Column, Integer, Float, String, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import UniqueConstraint

Base = declarative_base()

class Player(Base):

    __tablename__ = 'players'
    id = Column(Integer, primary_key=True)
    type = Column(String(20))

    retrosheet_id = Column(String(20))
    mlb_id = Column(String(20))
    pecota_id = Column(String(20))
    fangraphs_id = Column(String(20))
    br_id = Column(String(20))

    last_name = Column(String(50))
    first_name = Column(String(50))
    birthdate = Column(Date)

    __mapper_args__ = {
        'polymorphic_identity': 'players',
        'polymorphic_on': type
    }

class Batter(Player):

    __tablename__ = 'batters'
    id = Column(String(20), ForeignKey('players.id'), primary_key=True)
    projections = relationship('BatterProjection', backref='batters')

    __mapper_args__ = {
        'polymorphic_identity': 'batters'
    }

    def __repr__(self):
        return '<Batter %d (%s, %s)>' % (self.id, self.last_name, self.first_name)

class Pitcher(Player):

    __tablename__ = 'pitchers'
    id = Column(String(20), ForeignKey('players.id'), primary_key=True)
    projections = relationship('PitcherProjection', backref='pitchers')

    __mapper_args__ = {
        'polymorphic_identity': 'pitchers'
    }

    def __repr__(self):
        return '<Pitcher %d (%s, %s)>' % (self.id, self.last_name, self.first_name)

class ProjectionSystem(Base):

    __tablename__ = 'projection_systems'
    id = Column(Integer, primary_key=True)

    name = Column(String(20))
    year = Column(Integer)
    UniqueConstraint('name', 'year')
    batter_projections = relationship('BatterProjection')
    pitcher_projections = relationship('PitcherProjection')

    def __repr__(self):
        return '<ProjectionSystem %d (%s, %d)>' % (id, name, year)

class BatterProjection(Base):

    __tablename__ = 'batter_projections'
    id = Column(Integer, primary_key=True)
    batter_id = Column(Integer, ForeignKey('batters.id'))
    projection_id = Column(Integer, ForeignKey('projection_systems.id'))
    UniqueConstraint('batter_id', 'projection_id')

    team = Column(String(3))

    pa = Column(Integer)
    ab = Column(Integer)
    r = Column(Integer)
    rbi = Column(Integer)
    h = Column(Integer)
    h2b = Column(Integer)
    h3b = Column(Integer)
    hr = Column(Integer)
    sb = Column(Integer)
    cs = Column(Integer)
    bb = Column(Integer)
    k = Column(Integer)
    hbp = Column(Integer)
    sac = Column(Integer)
    sf = Column(Integer)

    def __repr__(self):
        return '<BatterProjection %d>' % (self.id)

class PitcherProjection(Base):

    __tablename__ = 'pitcher_projections'
    id = Column(Integer, primary_key=True)
    pitcher_id = Column(Integer, ForeignKey('pitchers.id'))
    projection_id = Column(Integer, ForeignKey('projection_systems.id'))
    UniqueConstraint('pitcher_id', 'projection_id')

    w = Column(Integer)
    l = Column(Integer)
    ip = Column(Float)
    h = Column(Integer)
    r = Column(Integer)
    er = Column(Integer)
    hr = Column(Integer)
    bb = Column(Integer)
    k = Column(Integer)
    wp = Column(Integer)
    hbp = Column(Integer)

    def __repr__(self):
        return '<PitcherProjection %d>' % (self.id)