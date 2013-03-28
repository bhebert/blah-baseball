from projections import *
from sklearn.linear_model import LassoLarsCV
import numpy
import numpy.ma
import random
import csv
from baseballprojections.aux_vars import *

base_dir = "C:\\Users\\Benjamin\\Dropbox\\Baseball\\CSVs for DB"
#base_dir = "/Users/andrew_lim/Dropbox/Baseball/CSVs for DB"


pm = MyProjectionManager('sqlite:///projections.db')
#pm = MyProjectionManager()
#pm.read_everything_csv(base_dir = base_dir)

player_types = ['batter','pitcher']
playing_times = {'batter':'pa', 'pitcher':'g'}
stats = {'batter':['pa', 'ab', 'obp', 'slg', 'sbrate', 'csrate', 'runrate', 'rbirate'],
         'pitcher':['g','gs','ip','era','whip','sv','winrate','krate']}
proj_systems = ['pecota', 'zips', 'steamer']
proj_systems_sv = ['pecota','steamer']

cv_num = 10
min_pts ={'batter':300, 'pitcher':15}

proj_years = [2011, 2012]
curr_year = 2013

stat_functions = { stat: None for stat in (set(stats['batter']) | set(stats['pitcher'])) }
def stat_ops(p):
    if p.obp is not None and p.slg is not None:
        return p.obp + p.slg
    else:
        return None
def stat_runrate(p):
    if p.pa is not None and p.r is not None and p.pa > 0:
        return p.r / p.pa
    else:
        return None
def stat_rbirate(p):
    if p.pa is not None and p.rbi is not None and p.pa > 0:
        return p.rbi / p.pa
    else:
        return None
def stat_sbrate(p):
    if p.pa is not None and p.sb is not None and p.pa > 0 and p.obp is not None and p.obp > 0:
        return p.sb / (p.pa*p.obp)
    else:
        return None
def stat_csrate(p):
    if p.pa is not None and p.cs is not None and p.pa > 0 and p.obp is not None and p.obp > 0:
        return p.cs / (p.pa*p.obp)
    else:
        return None
def stat_saverate(p):
    if p.g is not None and p.gs is not None and (p.g-p.gs) > 0 and p.sv is not None:
        return p.sv / (p.g-p.gs)
    elif p.g is not None and p.gs is not None and p.sv is not None:
        return 0
    else:
        return None
def stat_winrate(p):
    if p.g is not None and p.w is not None and p.g > 0:
         return p.w / p.g
    else:
         return None
def stat_krate(p):
    if p.k is not None and p.ip is not None and p.ip > 0:
         return p.k / p.ip
    else:
         return None
stat_functions['ops'] = stat_ops
stat_functions['runrate'] = stat_runrate
stat_functions['rbirate'] = stat_rbirate
stat_functions['sbrate'] = stat_sbrate
stat_functions['csrate'] = stat_csrate
stat_functions['saverate'] = stat_saverate
stat_functions['winrate'] = stat_winrate
stat_functions['krate'] = stat_krate

for player_type in player_types:
    csvfile = player_type + "Projs.csv"
    playing_time = playing_times[player_type]

    # This is the sample of players to forecast
    if player_type == 'batter':
        players = pm.batter_projection_groups(filter_clause=ProjectionSystem.year==curr_year)
    else:
        players = pm.pitcher_projection_groups(filter_clause=ProjectionSystem.year==curr_year)

    first_names = {}
    last_names = {}
    mlb_ids = {}
    positions = {}
    for player, pairs in players:
        key = str(player.mlb_id) + "_" + str(curr_year)
        first_names[key] = player.first_name
        last_names[key] = player.last_name
        mlb_ids[key] = player.mlb_id
        for (_, projection) in pairs:
            sys = projection.projection_system
            if sys.name == 'steamer' :
                 if player_type == 'batter':
                    positions[key] = getattr(projection,'positions')
                 else:
                    positions[key] = 'P' 


    # This makes a model for choosing the sample    

    pt_projs = pm.get_player_year_data(proj_years, proj_systems,
                                       player_type, [playing_time],
                                       stat_functions)[playing_time]
    pt_actuals = pm.get_player_year_data(proj_years, ['actual'],
                                         player_type, [playing_time],
                                         stat_functions)[playing_time]

    player_years = list(set(pt_actuals.keys()) & set(pt_projs.keys()))
    random.shuffle(player_years)

    ivars = []
    depvars = []

    for pyear in player_years:
        ivars.append([pt_projs[pyear][system] for system in proj_systems])
        depvars.append(pt_actuals[pyear]['actual'])

    x = numpy.array(ivars)
    
    y = numpy.array(depvars)

    model_pt = LassoLarsCV(cv=cv_num)
    model_pt.fit(x,y)

    print "Rough PT model, to choose sample"
    print model_pt.coef_
    print model_pt.intercept_

    sample_proj_pt_arr = model_pt.predict(x)

    sample_proj_pt = dict(zip(player_years,sample_proj_pt_arr))

    models = {}
    final_projs = {}

    ivars = {}
    depvars = {}

    for stat in stats[player_type]:

        proj_stats = [stat]
        
        if stat in ['sv','g','gs']:
            psystems = proj_systems_sv
            proj_stats = ['sv','g','gs','krate','era']
        else:
            psystems = proj_systems
            
            
        projs = pm.get_player_year_data(proj_years, psystems,
                                        player_type, proj_stats,
                                        stat_functions)
            
        actuals = pm.get_player_year_data(proj_years, ['actual'],
                                          player_type, [stat],
                                          stat_functions)[stat]

        pset = set(actuals.keys())
        for st in proj_stats:
            pset = pset & set(projs[st].keys())
        player_years = list(pset)
        fp_years = filter(lambda k: k in sample_proj_pt and sample_proj_pt[k] > min_pts[player_type], player_years)
        random.shuffle(fp_years)

        ivars[stat] = []
        depvars[stat] = []

        for pyear in fp_years:
            row = []
            for st in proj_stats:
                row.extend(projs[st][pyear][system] for system in psystems)
            ivars[stat].append(row)
            depvars[stat].append(actuals[pyear]['actual'])

        x = numpy.array(ivars[stat])
        y = numpy.array(depvars[stat])

        yrs = get_year_var(fp_years,proj_years)
        rookies = get_rookie_var(fp_years,proj_years,'actual',player_type,pm)

        aux = numpy.hstack((yrs,rookies))
        aux2 = add_quad_interactions(aux)
        x = get_final_regs(x,aux2)        


        models[stat] = LassoLarsCV(cv=cv_num)
        models[stat].fit(x,y)

        print "Model for " + stat
        print "Num of player-seasons in sample: " + str(len(fp_years))
        print models[stat].coef_
        print models[stat].intercept_

    ivars2 = {}

    for stat in stats[player_type]:
        proj_stats = [stat]
        if stat in ['sv','g','gs']:
            psystems = proj_systems_sv
            proj_stats = ['sv','g','gs','krate','era']
        else:
            psystems = proj_systems

      
        projs = pm.get_player_year_data([curr_year], psystems, 
                                        player_type, proj_stats, 
                                        stat_functions)

        pset = set(projs[stat].keys())
        for st in proj_stats:
            pset = pset & set(projs[st].keys())
        player_years = list(pset)

        ivars2[stat] = []
        for pyear in player_years:
            row = []
            for st in proj_stats:
                row.extend(projs[st][pyear][system] for system in psystems)
            ivars2[stat].append(row)
            
     
        x = numpy.array(ivars2[stat])


        yrs = get_year_var(player_years,proj_years)
        rookies = get_rookie_var(player_years,[curr_year],'pecota',player_type,pm)

        aux = numpy.hstack((yrs,rookies))
        aux2 = add_quad_interactions(aux)
        x = get_final_regs(x,aux2)
        
        
        final_stat_proj = models[stat].predict(x)
        final_projs[stat] = dict(zip(player_years,final_stat_proj))

    cols = ['mlb_id','last_name','first_name','positions']
    cols.extend(stats[player_type])

    with open(csvfile, 'wb') as f:

        writer = csv.DictWriter(f, cols)
        writer.writeheader()

        player_years.sort(key=lambda k: final_projs[playing_time][k])
        player_years.reverse()

        for k in player_years:
            row = {'mlb_id': mlb_ids[k] ,
                   'first_name': first_names[k],
                   'last_name': last_names[k],
                   'positions': positions[k],
                   }
            for stat in stats[player_type]:
                row[stat] = final_projs[stat][k]
            writer.writerow(row)

