
# blah-baseball

Python program to load projections into a database. 

Requirements (suggested version number in parentheses, though older versions may work): 

- Python (2.7.3)
- SQLAlchemy (0.8.0b2)

For databases I used SQLite3 (3.7.14.1) but you should be OK with anything that SQLAlchemy supports. 

### To-do

- Allow projection of calculated stats directly, for example for projections that only provide SLG and not the constituent stats
- Add more reader functions/check raw files
- Add CSV generator
- Test runs! Add some reconciliation