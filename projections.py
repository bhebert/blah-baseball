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

class MyProjectionManager(ProjectionManager):

    # PECOTA readers

    def read_pecota_batters_2011(self, filename, verbose=False):

        header_row = ['mlb_id', '', 'last_name', 'first_name', 'team', '', '', 
                      '', '', '', '', 'birthdate', '', 'pa', 'ab', 'r', 'h1b', 
                      'h2b', 'h3b', 'hr', 'rbi', 'bb', 'hbp', 'k', 'sb', 'cs', 
                      'sac', 'sf']

        calculated_key = {
            'birthdate': lambda x: datetime.datetime.strptime(x['birthdate'], '%m/%d/%Y'),
            'h': lambda x: sum(map(int, [x['h1b'], x['h2b'], x['h3b'], x['hr']])),
        }
        self.read_projection_csv(filename, 'pecota', 2011, 'batter',
                                 header_row, calculated_key,
                                 verbose=verbose)

    def read_pecota_batters_2012(self, filename, verbose=False):

        header_row = ['mlb_id', 'bp_id', 'last_name', 'first_name', '', '', '',
                      '', '', '', 'team', '', '', '', 'pa', 'ab', 'r', 'h1b', 
                      'h2b', 'h3b', 'hr', 'h', '', 'rbi', 'bb', 'hbp', 'k', 
                      'sac', 'sf', '', 'sb', 'cs']
        calculated_key = {}
        self.read_projection_csv(filename, 'pecota', 2012, 'batter',
                                 header_row, calculated_key,
                                 verbose=verbose)

    def read_pecota_batters_2013(self, filename, verbose=False):

        header_row = ['mlb_id', '', 'bp_id', 'last_name', 'first_name', '', '', 
                      '', '', '', '', 'team', '', '', '', 'pa', 'ab', 'r', 
                      'h1b', 'h2b', 'h3b', 'hr', 'h', '', 'rbi', 'bb', 'hbp', 
                      'k', 'sac', 'sf', '', 'sb', 'cs']
        calculated_key = {}
        self.read_projection_csv(filename, 'pecota', 2013, 'batter',
                                 header_row, calculated_key,
                                 verbose=verbose)

    # ZIPS readers

    def read_zips_batters_2011(self, filename, verbose=False):

        header_row = ['mlb_id', '', 'last_name', 'first_name', 'team', '', '', 
                      '', '', '', 'avg', 'obp', 'slg', '', 'ab', 'r', 'h', 
                      'h2b', 'h3b', 'hr', 'rbi', 'bb', 'k', 'hbp', 'sb', 'cs', 
                      'sac', 'sf', '', '', '', 'pa']

        calculated_key = {}
        self.read_projection_csv(filename, 'zips', 2011, 'batter',
                                 header_row, calculated_key,
                                 verbose=verbose)

    def read_zips_batters_2012(self, filename, verbose=False):

        header_row = ['mlb_id', 'full_name', 'team', '', '', '', 'avg', 'obp', 
                      'slg', '', 'ab', 'r', 'h', 'h2b', 'h3b', 'hr', 'rbi', 
                      'bb', 'k', 'hbp', 'sb', 'cs', 'sac', 'sf', '', '', '', 'pa']

        calculated_key = {
            'last_name': last_name_from_full_name,
            'first_name': first_name_from_full_name,
        }
        self.read_projection_csv(filename, 'zips', 2012, 'batter',
                                 header_row, calculated_key,
                                 verbose=verbose)

    def read_zips_batters_2013(self, filename, verbose=False):

        header_row = ['mlb_id', 'full_name', 'team', '', '', '', 'avg', 'obp', 
                      'slg', '', 'pa', 'ab', 'r', 'h', 'h2b', 'h3b', 'hr', 
                      'rbi', 'bb', 'k', 'hbp', 'sb', 'cs', 'sac', 'sf']

        calculated_key = {
            'last_name': last_name_from_full_name,
            'first_name': first_name_from_full_name,
        }
        self.read_projection_csv(filename, 'zips', 2013, 'batter',
                                 header_row, calculated_key,
                                 verbose=verbose)

    # Steamer readers

    def read_steamer_batters_2011(self, filename, verbose=False):

        header_row = ['mlb_id', 'full_name', '', 'team', '', '', '', '', '', 
                      '', 'bb', 'hbp', 'sac', 'sf', 'ab', 'k', '', 'h', 'h1b', 
                      'h2b', 'h3b', 'hr', '', 'sb', 'cs', 'avg', 'obp', 
                      'slg', 'ops', '', 'r', 'rbi', 'pa']

        calculated_key = {
            'last_name': last_name_from_full_name,
            'first_name': first_name_from_full_name,
        }
        self.read_projection_csv(filename, 'steamer', 2011, 'batter',
                                 header_row, calculated_key,
                                 verbose=verbose)

    def read_steamer_batters_2012(self, filename, verbose=False):

        header_row = ['mlb_id', 'full_name', '', '', '', '', '', 'team', '', 
                      '', '', 'pa', 'ab', 'bb', 'hbp', 'sac', 'sf', 'k', '', 
                      'h', 'h3b', 'h2b', 'h1b', 'hr', 'r', 'rbi', 'sb', 'cs',
                      'avg', 'obp', 'slg']

        calculated_key = {
            'last_name': last_name_from_full_name,
            'first_name': first_name_from_full_name,
        }
        self.read_projection_csv(filename, 'steamer', 2012, 'batter',
                                 header_row, calculated_key,
                                 verbose=verbose)

    def read_steamer_batters_2013(self, filename, verbose=False):

        header_row = ['mlb_id', 'first_name', 'last_name', '', '', '', 'team', 
                      'pa', '', '', 'bb', 'k', 'hbp', '', 'sac', 'sf', 'ab', 
                      'h', 'h1b', 'h2b', 'h3b', 'hr', 'avg', 'obp', 'slg', 
                      'sb', 'cs', 'r', 'rbi']

        calculated_key = {}
        self.read_projection_csv(filename, 'steamer', 2013, 'batter',
                                 header_row, calculated_key,
                                 verbose=verbose)
