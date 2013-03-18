
# blah-baseball

Python program to load projections into a database. 

Requirements (suggested version number in parentheses, though older versions may work): 

- Python 2 (2.7.3)
- SQLAlchemy (0.8.0b2)

For databases I used SQLite3 (3.7.14.1) but you should be OK with anything that SQLAlchemy supports. 

### Usage

Simple example from the console, creates an in-memory (SQLite3) db, reads CSV files. File locations and formats are specified in `projections.py`. 

    > execfile('projections.py')
    > x = MyProjectionManager()
    > x.read_everything_csv()
    Reading PECOTA 2011...
    Reading PECOTA 2012...
    Reading PECOTA 2013...
    Reading Steamer 2011...
    Reading Steamer 2012...
    Reading Steamer 2013...

    > x.query(Batter).filter(Batter.last_name == 'pujols')
    <sqlalchemy.orm.query.Query at 0x103393510>
    > pujols = x.query(Batter).filter(Batter.last_name == 'pujols').first()
    > pujols.prettyprint()
    pujols, albert (id: 873, MLB ID: 405395)
    Projections (OBP SLG HR R RBI SB):
           pecota_batter, 2011 : 0.423 0.581  37 108 110  11
           pecota_batter, 2012 : 0.404 0.558  37 106 110  11
           pecota_batter, 2013 : 0.383 0.553  36 100 110  10
          steamer_batter, 2011 : 0.423 0.594  35 104 106   7
          steamer_batter, 2012 : 0.403 0.597  40 111 125   7
          steamer_batter, 2013 : 0.379 0.559  36 101 113   6


### To-do

- ZIPS name-matching issue (why wouldn't you include an ID field?!)
- Actuals
- Try it out with non-in-memory dbs (should just work, but worth testing)
- Add CSV generator
- Rewrite this README
