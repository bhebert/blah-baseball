from sqlalchemy import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship, backref

Base = declarative_base()

class Player(Base):

    __tablename__ = 'players'
    id = Column(Integer, primary_key=True)

    retrosheet_id = Column(String(20))
    mlb_id = Column(Integer)
    pecota_id = Column(Integer)
    fangraphs_id = Column(Integer)
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
    id = Column(Integer, ForeignKey('players.id'), primary_key=True)
    projections = relationship('BatterProjection', backref='batters')

    __mapper_args__ = {
        'polymorphic_identity': 'batter'
    }

class Pitcher(Player):

    __tablename__ = 'pitchers'
    id = Column(Integer, ForeignKey('players.id'), primary_key=True)
    projections = relationship('PitcherProjection', backref='pitchers')

    __mapper_args__ = {
        'polymorphic_identity': 'pitcher'
    }

class ProjectionSystem(Base):

    __tablename__ = 'projection_systems'
    id = Column(Integer, primary_key=True)

    name = Column(String)
    year = Column(Integer)

class BatterProjection(Base):

    __tablename__ = 'batter_projections'
    id = Column(Integer, primary_key=True)
    batter_id = Column(Integer, ForeignKey('batters.id'))

    # associated projection system
    # start of season team

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

class PitcherProjection(Base):

    __tablename__ = 'pitcher_projections'
    id = Column(Integer, primary_key=True)

    # associated pitcher
    # associated projection system

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
