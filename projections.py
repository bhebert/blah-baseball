from baseballprojections import *
import datetime

# Helper functions

def split_full_name(full_name, sep=' '):
    return full_name.split(sep)

def first_name_from_full_name(full_name, sep=' '):
    split_result = split_full_name(full_name, sep=sep)
    if len(split_result) == 0: return None
    else: return split_result[0]

def last_name_from_full_name(full_name, sep=' '):
    split_result = split_full_name(full_name, sep=sep)
    if len(split_result) < 1: return None
    else: return split_result[1]

def batter_post_processor(x, strptime_format='%m/%d/%Y', 
                          try_soft_obp=True):

    # Type conversion not needed for SQLAlchemy, but is needed below when we
    # try to compute calculated fields. 
    for k in ('h', 'h1b', 'h2b', 'h3b', 'hr', 'ab', 'pa', 'bb', 'hbp', 'sf'):
        if k in x and x[k] is not None and x[k] != '':
            x[k] = int(x[k])

    if 'birthdate' in x and 'birthdate' is not None and 'birthdate' != '':
        x['birthdate'] = datetime.datetime.strptime(x['birthdate'], '%m/%d/%Y')

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
            try: x['obp'] = (x['h'] + x['bb'] + x['hbp']) / float(x['pa'])
            except: pass
        else: 
            pass

    return x

class MyProjectionManager(ProjectionManager):

    # PECOTA readers

    def read_pecota_batters_2011(self, filename, verbose=False):

        header_row = ['mlb_id', '', 'last_name', 'first_name', 'team', '', '', 
                      '', '', '', '', 'birthdate', '', 'pa', 'ab', 'r', 'h1b', 
                      'h2b', 'h3b', 'hr', 'rbi', 'bb', 'hbp', 'k', 'sb', 'cs', 
                      'sac', 'sf']
        self.read_projection_csv(filename, 'pecota', 2011,
                                 is_actual=False,
                                 player_type='batter',
                                 header_row=header_row, 
                                 post_processor=batter_post_processor,
                                 verbose=verbose)

    def read_pecota_batters_2012(self, filename, verbose=False):

        header_row = ['mlb_id', 'bp_id', 'last_name', 'first_name', '', '', '',
                      '', '', '', 'team', '', '', '', 'pa', 'ab', 'r', 'h1b', 
                      'h2b', 'h3b', 'hr', 'h', '', 'rbi', 'bb', 'hbp', 'k', 
                      'sac', 'sf', '', 'sb', 'cs']
        self.read_projection_csv(filename, 'pecota', 2012, 
                                 is_actual=False,
                                 player_type='batter',
                                 header_row=header_row, 
                                 post_processor=batter_post_processor,
                                 verbose=verbose)

    def read_pecota_batters_2013(self, filename, verbose=False):

        header_row = ['mlb_id', '', 'bp_id', 'last_name', 'first_name', '', '', 
                      '', '', '', '', 'team', '', '', '', 'pa', 'ab', 'r', 
                      'h1b', 'h2b', 'h3b', 'hr', 'h', '', 'rbi', 'bb', 'hbp', 
                      'k', 'sac', 'sf', '', 'sb', 'cs']
        self.read_projection_csv(filename, 'pecota', 2013, 
                                 is_actual=False,
                                 player_type='batter',
                                 header_row=header_row, 
                                 post_processor=batter_post_processor,
                                 verbose=verbose)

    # ZIPS readers

    def read_zips_batters_2011(self, filename, verbose=False):

        header_row = ['mlb_id', '', 'last_name', 'first_name', 'team', '', '', 
                      '', '', '', 'avg', 'obp', 'slg', '', 'ab', 'r', 'h', 
                      'h2b', 'h3b', 'hr', 'rbi', 'bb', 'k', 'hbp', 'sb', 'cs', 
                      'sac', 'sf', '', '', '', 'pa']
        self.read_projection_csv(filename, 'zips', 2011, 
                                 is_actual=False,
                                 player_type='batter',
                                 header_row=header_row, 
                                 post_processor=batter_post_processor,
                                 verbose=verbose)

    def read_zips_batters_2012(self, filename, verbose=False):

        header_row = ['mlb_id', 'full_name', 'team', '', '', '', 'avg', 'obp', 
                      'slg', '', 'ab', 'r', 'h', 'h2b', 'h3b', 'hr', 'rbi', 
                      'bb', 'k', 'hbp', 'sb', 'cs', 'sac', 'sf', '', '', '', 'pa']
        self.read_projection_csv(filename, 'zips', 2012, 
                                 is_actual=False,
                                 player_type='batter',
                                 header_row=header_row, 
                                 post_processor=batter_post_processor,
                                 verbose=verbose)

    def read_zips_batters_2013(self, filename, verbose=False):

        header_row = ['mlb_id', 'full_name', 'team', '', '', '', 'avg', 'obp', 
                      'slg', '', 'pa', 'ab', 'r', 'h', 'h2b', 'h3b', 'hr', 
                      'rbi', 'bb', 'k', 'hbp', 'sb', 'cs', 'sac', 'sf']
        self.read_projection_csv(filename, 'zips', 2013, 
                                 is_actual=False,
                                 player_type='batter',
                                 header_row=header_row, 
                                 post_processor=batter_post_processor,
                                 verbose=verbose)

    # Steamer readers

    def read_steamer_batters_2011(self, filename, verbose=False):

        header_row = ['mlb_id', 'full_name', '', 'team', '', '', '', '', '', 
                      '', 'bb', 'hbp', 'sac', 'sf', 'ab', 'k', '', 'h', 'h1b', 
                      'h2b', 'h3b', 'hr', '', 'sb', 'cs', 'avg', 'obp', 
                      'slg', 'ops', '', 'r', 'rbi', 'pa']
        self.read_projection_csv(filename, 'steamer', 2011, 
                                 is_actual=False,
                                 player_type='batter',
                                 header_row=header_row, 
                                 post_processor=batter_post_processor,
                                 verbose=verbose)

    def read_steamer_batters_2012(self, filename, verbose=False):

        header_row = ['mlb_id', 'full_name', '', '', '', '', '', 'team', '', 
                      '', '', 'pa', 'ab', 'bb', 'hbp', 'sac', 'sf', 'k', '', 
                      'h', 'h3b', 'h2b', 'h1b', 'hr', 'r', 'rbi', 'sb', 'cs',
                      'avg', 'obp', 'slg']
        self.read_projection_csv(filename, 'steamer', 2012, 
                                 is_actual=False,
                                 player_type='batter',
                                 header_row=header_row, 
                                 post_processor=batter_post_processor,
                                 verbose=verbose)

    def read_steamer_batters_2013(self, filename, verbose=False):

        header_row = ['mlb_id', 'first_name', 'last_name', '', '', '', 'team', 
                      'pa', '', '', 'bb', 'k', 'hbp', '', 'sac', 'sf', 'ab', 
                      'h', 'h1b', 'h2b', 'h3b', 'hr', 'avg', 'obp', 'slg', 
                      'sb', 'cs', 'r', 'rbi']
        self.read_projection_csv(filename, 'steamer', 2013, 
                                 is_actual=False,
                                 player_type='batter',
                                 header_row=header_row, 
                                 post_processor=batter_post_processor,
                                 verbose=verbose)
