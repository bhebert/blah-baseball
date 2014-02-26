
# blah-baseball

Python program to load baseball projections into a database. (Not written for the general public in mind, in case you've stumbled onto this)

Requirements (suggested version number in parentheses, though older versions may work): 

- Python 3 (3.3.4)
- SQLAlchemy (0.9.3)

For databases I used SQLite3 (3.7.14.1) but you should be OK with anything that SQLAlchemy supports. 

### Basic use

Look at `projections.py` for our example. More generally, to use this, you'd create a file like `projections.py` that creates a new subclass of `ProjectionManager` and also includes several CSV readers and/or line processors (in case each line has to be processed before load, for example if you've only got HR/9 and you want HR) that fit the data format of your files. 

If you want to add any new projections, just add some new CSV readers in the same format to `projections.py` and also add a line to call it in the method `read_everything_csv`. 

### Database creation

Easiest to work from the Python prompt IMHO and start off everything with

    > execfile('projections.py')

Example that creates a database `projections.db`. The argument to `MyProjectionManager` matches whatever [SQLAlchemy allows](http://docs.sqlalchemy.org/en/rel_0_8/core/engines.html), and if you leave it blank it'll create an in-memory SQLite3 database. 

    > x = MyProjectionManager('sqlite:///projections.db')
    > base_dir = '/Users/andrew_lim/Dropbox/Baseball/CSVs for DB'  # replace with your location
    > x.read_everything_csv(base_dir=base_dir)
    Reading PECOTA 2011...
    Reading PECOTA 2012...
    Reading PECOTA 2013...
    Reading Steamer 2011...
    Reading Steamer 2012...
    Reading Steamer 2013...
    Reading ZIPS 2011...
    Reading ZIPS 2012...
    Reading ZIPS 2013...

Once you've got the db, you can bring it back easily at the prompt

    > x = MyProjectionManager('sqlite:///projections.db')

You can call query on the `ProjectionManager` object, for example:

    > x.query(Batter).filter(Batter.last_name.like('Pujols'))
    <sqlalchemy.orm.query.Query at 0x10bdca790>
    > pujols = x.query(Batter).filter(Batter.last_name.like('Pujols')).first()
    > pujols
    <Batter 873 (pujols, albert)>
    > pujols.prettyprint()
    pujols, albert (id: 873, MLB ID: 405395)

                Projection :   OBP   SLG  HR   R RBI  SB
              pecota, 2011 : 0.423 0.581  37 108 110  11
              pecota, 2012 : 0.404 0.558  37 106 110  11
              pecota, 2013 : 0.383 0.553  36 100 110  10
             steamer, 2011 : 0.423 0.594  35 104 106   7
             steamer, 2012 : 0.403 0.597  40 111 125   7
             steamer, 2013 : 0.379 0.559  36 101 113   6
                zips, 2011 : 0.419 0.592  37 100 107  12
                zips, 2012 : 0.388 0.564  37  99 100  11
                zips, 2013 : 0.359 0.516  31  88  94  10
              pecota, 2011 : 0.423 0.581  37 108 110  11
              pecota, 2012 : 0.404 0.558  37 106 110  11
              pecota, 2013 : 0.383 0.553  36 100 110  10
             steamer, 2011 : 0.423 0.594  35 104 106   7
             steamer, 2012 : 0.403 0.597  40 111 125   7
             steamer, 2013 : 0.379 0.559  36 101 113   6
                zips, 2011 : 0.419 0.592  37 100 107  12
                zips, 2012 : 0.388 0.564  37  99 100  11
                zips, 2013 : 0.359 0.516  31  88  94  10

To generate a cross-projection CSV, for example for OBP and HR of batters with last name Molina: 

    > x.cross_projection_csv('molina.csv', 'batter', ['obp', 'hr'], filter_clause=Batter.last_name.like("Molina"), verbose=True)

This generates a file that looks like the `molina.csv` file included in the repo. The filter clause is optional, omitting it in the above example would have generated the file for all batters. 