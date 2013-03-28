import datetime
import re
from sqlalchemy.orm.attributes import InstrumentedAttribute

def getSQLAlchemyFields(classname):
    attribs = classname.__dict__.iteritems()
    attribs = filter(lambda (k,v): type(v) is InstrumentedAttribute, attribs)
    return map(lambda (x,_): x, attribs)

def split_lastname_firstname_comma(full_name):
    splitname = full_name.split(',')
    if len(splitname) == 1:
        return ('', splitname[0].strip())
    return (splitname[1].strip(), splitname[0].strip())

def split_firstname_lastname_space(full_name):
    splitname = full_name.split(' ')
    if len(splitname) == 1:
        return ('', splitname[1].strip())
    return (splitname[0].strip(), ' '.join(splitname[1:]).strip())

def simple_name(name):
    return re.sub(r'\W', '', name).lower()

# to see all the teams:
# sorted(set(map(lambda x: x.team, pm.query(BatterProjection))))

valid_teams = [
    u'ARI',
    u'ATL',
    u'BAL',
    u'BOS',
    u'CHC',
    u'CHW',
    u'CIN',
    u'CLE',
    u'COL',
    u'DET',
    u'HOU',
    u'KC',
    u'LAA',
    u'LAD',
    u'MIA',
    u'MIL',
    u'MIN',
    u'NYM',
    u'NYY',
    u'OAK',
    u'PHI',
    u'PIT',
    u'SD',
    u'SEA',
    u'SF',
    u'STL',
    u'TB',
    u'TEX',
    u'TOR',
    u'WAS',
    u'FA',
]

team_remaps = {
    'Angels': 'LAA',
    'Astros': 'HOU',
    'Athletics': 'OAK',
    'Blue Jays': 'TOR',
    'Braves': 'ATL',
    'Brewers': 'MIL',
    'Cardinals': 'STL',
    'Cubs': 'CHC',
    'Diamondbacks': 'ARI',
    'Dodgers': 'LAD',
    'Giants': 'SF',
    'Indians': 'CLE',
    'Mariners': 'SEA',
    'Marlins': 'MIA',
    'Mets': 'NYM',
    'Nationals': 'WAS',
    'Orioles': 'BAL',
    'Padres': 'SD',
    'Phillies': 'PHI',
    'Pirates': 'PIT',
    'Rangers': 'TEX',
    'Rays': 'TB',
    'Red Sox': 'BOS',
    'Reds': 'CIN',
    'Rockies': 'COL',
    'Royals': 'KC',
    'Tigers': 'DET',
    'Twins': 'MIN',
    'White Sox': 'CHW',
    'Yankees': 'NYY',
    'none': 'FA',
    'ANA': 'LAA',
    'CHA': 'CHW',
    'CHN': 'CHC',
    'FLO': 'MIA',
    'KCA': 'KC',
    'KCR': 'KC',
    'LAN': 'LAD',
    'NYA': 'NYY',
    'NYN': 'NYM',
    'SDN': 'SD',
    'SDP': 'SD',
    'SFG': 'SF',
    'SFN': 'SF',
    'SLN': 'STL',
    'TBA': 'TB',
    'TBR': 'TB',
    'WSN': 'WAS',
    '': 'FA',
    '- - -': 'FA',
}

def basic_post_processor(x, 
                         name_handler=split_firstname_lastname_space,
                         strptime_format='%m/%d/%Y'):

    if 'birthdate' in x and x['birthdate'] is not None and x['birthdate'] != '':
        try: x['birthdate'] = datetime.datetime.strptime(x['birthdate'], strptime_format)
        except: del x['birthdate']

    if 'last_name' in x and x['last_name'] is not None:
        x['last_name'] = simple_name(x['last_name'])
    if 'first_name' in x and x['first_name'] is not None:
        x['first_name'] = simple_name(x['first_name'])

    if 'full_name' in x and 'full_name' is not None and 'full_name' != '':
        (first_name, last_name) = name_handler(x['full_name'])
        if 'last_name' not in x or ('last_name' is None and 'last_name' != ''):
            x['last_name'] = simple_name(last_name)
        if 'first_name' not in x or ('first_name' is None and 'first_name' != ''):
            x['first_name'] = simple_name(first_name)

    if 'team' in x and x['team'] is not None and x['team'] != '':
        if x['team'] in team_remaps:
            x['team'] = team_remaps[x['team']]
    else:
        x['team'] = 'FA'

    return x

def batter_post_processor(x, 
                          name_handler=split_firstname_lastname_space,
                          strptime_format='%m/%d/%Y', 
                          try_soft_obp=True):

    x = basic_post_processor(x, name_handler=name_handler, 
                             strptime_format=strptime_format)

    # Type conversion not needed for SQLAlchemy, but is needed below when we
    # try to compute calculated fields. 

    for k in ('h', 'h1b', 'h2b', 'h3b', 'hr', 'ab', 'pa', 'bb', 'hbp', 'sf'):
        if k in x and x[k] is not None and x[k] != '':
            x[k] = float(x[k])

    if 'h' not in x or x['h'] is None:
        try: x['h'] = x['h1b'] + x['h2b'] + x['h3b'] + x['hr']
        except: pass
    if 'h1b' not in x or x['h1b'] is None:
        try: x['h1b'] = x['h'] - x['h2b'] - x['h3b'] - x['hr']
        except: pass
    if 'h2b' not in x or x['h2b'] is None:
        try: x['h1b'] = x['h'] - x['h1b'] - x['h3b'] - x['hr']
        except: pass
    if 'h3b' not in x or x['h3b'] is None:
        try: x['h1b'] = x['h'] - x['h1b'] - x['h2b'] - x['hr']
        except: pass
    if 'hr' not in x or x['hr'] is None:
        try: x['h1b'] = x['h'] - x['h1b'] - x['h2b'] - x['h3b']
        except: pass

    try: x['avg'] = x['h'] / float(x['ab'])
    except: pass
    try: x['slg'] = (x['h1b'] + 2*x['h2b'] + 3*x['h3b'] + 4*x['hr']) / float(x['ab'])
    except: pass
    try:
        x['obp'] = (x['h'] + x['bb'] + x['hbp']) / \
                   float(x['ab'] + x['bb'] + x['hbp'] + x['sf'])
    except:
        if try_soft_obp:
            # technically inexact but should be really close
            try: x['obp'] = (x['h'] + x['bb'] + x['hbp']) / float(x['pa'])
            except: pass
        else: 
            pass

    return x

def pitcher_post_processor(x, 
                           name_handler=split_firstname_lastname_space,
                           strptime_format='%m/%d/%Y'):

    x = basic_post_processor(x, name_handler=name_handler, 
                             strptime_format=strptime_format)

    # Type conversion not needed for SQLAlchemy, but is needed below when we
    # try to compute calculated fields. 

    for k in ('r', 'ra', 'er', 'era', 'ip', 'whip', 'h', 'bb'):
        if k in x and x[k] is not None and x[k] != '':
            x[k] = float(x[k])

    if 'ra' not in x or x['ra'] is None:
        try: x['ra'] = x['r'] / x['ip']
        except: pass
    elif 'r' not in x or x['r'] is None:
        try: x['r'] = x['ra'] * x['ip']
        except: pass
    if 'era' not in x or x['era'] is None:
        try: x['era'] = x['er'] / x['ip']
        except: pass
    elif 'r' not in x or x['r'] is None:
        try: x['er'] = x['era'] * x['ip']
        except: pass
    if 'whip' not in x or x['whip'] is None:
        try: x['whip'] = (x['h'] + x['bb']) / x['ip']
        except: pass

    return x

def pitcher_post_processor_with_ip_fix(x, 
                                       name_handler=split_firstname_lastname_space,
                                       strptime_format='%m/%d/%Y'):

    x = pitcher_post_processor(x, name_handler=name_handler, 
                               strptime_format=strptime_format)
    if 'ip' in x and x['ip'] is not None:
        x['ip'] = float(int(x['ip']) + (x['ip'] - int(x['ip']))*10/3.0)
    return x