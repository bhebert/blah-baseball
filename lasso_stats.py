from projections import *
from sklearn.linear_model import LassoLarsCV, LassoCV
import itertools
import numpy
import numpy.ma
import random
import csv
from baseballprojections.aux_vars import *

# There are some warnings from scikit-learn
# This causes them to be ignored
import warnings
warnings.filterwarnings("ignore",category=DeprecationWarning)

#base_dir = "C:\\Users\\Benjamin\\Dropbox\\Baseball\\CSVs for DB"
#base_dir = "/Users/andrew_lim/Dropbox/Baseball/CSVs for DB"

base_dir = "/Users/bhebert/Dropbox/Baseball/CSVs for DB"



pm = MyProjectionManager('sqlite:///projections.db')

pm.read_everything_csv(base_dir = base_dir,verbose=False)

# what coefs get printed to stdout during the run
print_nonzero_coefs_only = True

#player_types = ['batter','pitcher']
#player_types = ['pitcher']
player_types = ['batter']
playing_times = {'batter':'pa', 'pitcher':'g'}
stats = {'batter':['pa', 'ab', 'obp', 'slg', 'sbrate', 'csrate', 'runrate', 'rbirate'],
         'pitcher':['g','gs','ip','era','whip','sv','winrate','krate']}
#stats = {'batter':['pa','sbrate'],'pitcher':['ip','era']}
        # 'pitcher':['g','era','krate']}
proj_systems = ['pecota', 'zips', 'steamer']
proj_systems_sv = ['pecota','steamer']

old_model = False

if old_model:

    cv_num = 10
    # This controls the weights of the "unusual" variables
    weight = 0.0001
    min_pts ={'batter':150, 'pitcher':15}

    # This is a dummy added in 2014 to control whether yrs get weight
    # This seems to produce terrible results. Not sure why.
    no_yr_weight = False
    use_lars = True
else:
    cv_num = 10;
    weight = 1;
    min_pts ={'batter':150, 'pitcher':15}
    no_yr_weight = False
    use_lars = False
    
    

proj_years = [2011, 2012, 2013]
curr_year = 2014

rmse_test = False

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
    elif p.pa is not None and p.sb is not None and p.pa > 0 and p.obp is not None and p.obp == 0:
        return 0
    else:
        return None
def stat_csrate(p):
    if p.pa is not None and p.cs is not None and p.pa > 0 and p.obp is not None and p.obp > 0:
        return p.cs / (p.pa*p.obp)
    elif p.pa is not None and p.cs is not None and p.pa > 0 and p.obp is not None and p.obp == 0:
        return 0
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

variances = {}

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
    fg_ids = {}
    positions = {}
    for player, pairs in players:
        key = str(player.fg_id) + "_" + str(curr_year)
        first_names[key] = player.first_name
        last_names[key] = player.last_name
        fg_ids[key] = player.fg_id
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

    pt_projs_curr = pm.get_player_year_data([curr_year], proj_systems,
                                       player_type, [playing_time],
                                       stat_functions)[playing_time]
    
    pt_actuals = pm.get_player_year_data(proj_years, ['actual'],
                                         player_type, [playing_time],
                                         stat_functions)[playing_time]

    player_years = list(set(pt_actuals.keys()) & set(pt_projs.keys()))
    random.shuffle(player_years)

    ivars = []
    ivars2 = []
    depvars = []
    columns = []

    for pyear in player_years:
        ivars.append([pt_projs[pyear][system] for system in proj_systems])
        depvars.append(pt_actuals[pyear]['actual'])

    for pyear in pt_projs_curr.keys():
        ivars2.append([pt_projs_curr[pyear][system] for system in proj_systems])

    x = numpy.array(ivars)
    x2 = numpy.array(ivars2)
    y = numpy.array(depvars)
    model_pt = LassoLarsCV(cv=cv_num)
    model_pt.fit(x,y)

    print("Rough PT model, to choose sample")
    for system, coef in zip(proj_systems, model_pt.coef_):
        print("%40s : %f" % (system, coef))
    print("%40s : %f" % ('intercept', model_pt.intercept_))

    sample_proj_pt_arr = model_pt.predict(x)

    curr_proj_pt_arr = model_pt.predict(x2)

    sample_proj_pt = dict(zip(player_years,sample_proj_pt_arr))
    curr_proj_pt = dict(zip(pt_projs_curr.keys(),curr_proj_pt_arr))

    models = {}
    final_projs = {}

    ivars = {}
    depvars = {}

    for stat in stats[player_type]:

        if old_model:
            proj_stats = stats[player_type]
        else:
            proj_stats = [stat]
            if stat in  ['sv','saverate']:
                proj_stats = [stat,'g','gs','era']
            
        projs = pm.get_player_year_data(proj_years, proj_systems,
                                        player_type, proj_stats,
                                        stat_functions)
            
        actuals = pm.get_player_year_data(proj_years, ['actual'],
                                          player_type, [stat],
                                          stat_functions)[stat]

        pset = set(actuals.keys())
        for st in proj_stats:
            pset = pset & set(projs[st].keys())
        player_years = list(pset)
        fp_years = list(filter(lambda k: k in sample_proj_pt and sample_proj_pt[k] > min_pts[player_type], player_years))
        random.shuffle(fp_years)

        ivars[stat] = []
        depvars[stat] = []
        coef_cols = []

        for st in proj_stats:
            systems2 = list(filter(lambda s: not ((st in ['sv','saverate']) and s=='zips'),proj_systems))
            for system in systems2:
                coef_cols.append("%s_%s" % (st, system))

        for pyear in fp_years:
            row = []
            for st in proj_stats:
                systems2 = list(filter(lambda s: not ((st in ['sv','saverate']) and s=='zips'),proj_systems))
                row.extend(projs[st][pyear][system] for system in systems2)
            ivars[stat].append(row)
            depvars[stat].append(actuals[pyear]['actual'])

        x = numpy.array(ivars[stat])
        y = numpy.array(depvars[stat])

        variances[stat] = numpy.std(y)
        w = weight * variances[stat]

        #print x
        
        # Normalize the other stats used
        j = 0
        for st in proj_stats:
            systems2 = filter(lambda s: not ((st in ['sv','saverate']) and s=='zips'),proj_systems)
            for system in systems2:
                if st != stat:
                    x[:,j] = standardize(x[:,j],w)
                j = j + 1
        #y = standardize(y,1)

        #print x
                
        # start adding in auxiliaries
        yrs =     get_year_var(fp_years, proj_years)
        if no_yr_weight:
             yrs =  yrs / weight           
        
        rookies = get_rookie_var(fp_years, proj_years, 'actual', player_type, pm)
        ages =    get_age_var(fp_years, proj_years, 'actual', player_type, pm,w)

        aux = numpy.hstack((yrs, rookies, ages))
        aux2 = add_quad_interactions(aux)
        

        teams   = get_team_vars(fp_years, proj_years, 'actual', player_type, pm)

        # this line would show fp_years with missing ages
        # print filter(lambda x: x[1][0] is None, zip(fp_years, ages))
        aux3 = numpy.hstack((aux2,teams))

        if old_model:
            x = get_final_regs(x,aux3,weight)
            aux_cols = ['yrs', 'rookies', 'age']
            aux_cols.extend(["%s * %s" % (c1, c2)
                    for (c1, c2) in itertools.combinations(aux_cols, 2)])
            aux_cols.extend(list(map(lambda team: 'team_%s' % team, helper.valid_teams[2:])))
        else:
            x = get_final_regs(x,yrs,weight)
            aux_cols = list(map(lambda yr: 'yr_lt_%d' % yr, proj_years[0:-1]))

 
        
        cross_cols = []
        for i in range(len(coef_cols)):
            for j in range(i, len(coef_cols)):
                cross_cols.append("%s * %s" % (coef_cols[i], coef_cols[j]))
            for aux_col in aux_cols:
                cross_cols.append("%s * %s" % (coef_cols[i], aux_col))

        coef_cols.extend(aux_cols)
        coef_cols.extend(cross_cols)

        if use_lars:
            models[stat] = LassoLarsCV(cv=cv_num, normalize=False)
        else:
            models[stat] = LassoCV(cv=cv_num, normalize=False)
        models[stat].fit(x,y)

        print("Model for " + stat)
        print("Num of player-seasons in sample: " + str(len(fp_years)))
        if len(coef_cols) != len(models[stat].coef_):
            print("WARNING COL MISMATCH")
        else:
            for coef_col, coef in zip(coef_cols, models[stat].coef_):
                if not (coef == 0 and print_nonzero_coefs_only):
                    print("%40s : %f" % (coef_col, coef))
            print("%40s : %f" % ('intercept', models[stat].intercept_))
        #print models[stat].coef_
        #print models[stat].intercept_

    ivars2 = {}
    depvars2 = {}
    ptvars = {}

    for stat in stats[player_type]:
        if old_model:
            proj_stats = stats[player_type]
        else:
            proj_stats = [stat]
            if stat in  ['sv','saverate']:
                proj_stats = [stat,'g','gs','era']
        
      
        projs = pm.get_player_year_data([curr_year], proj_systems, 
                                        player_type, proj_stats, 
                                        stat_functions)
        ptstat = playing_times[player_type]
        
        if rmse_test:

            actuals = pm.get_player_year_data([curr_year], ['actual'], 
                                        player_type, [stat], 
                                        stat_functions)

        

            actualspt = pm.get_player_year_data([curr_year], ['actual'], 
                                        player_type, [ptstat], 
                                        stat_functions)[ptstat]

            pset = set(actuals[stat].keys())
            pset = pset & set(actualspt.keys())
        else:
            pset = set(projs[stat].keys())
            
        for st in proj_stats:
            pset = pset & set(projs[st].keys())
        player_years2 = list(pset)

        player_years = list(filter(lambda k: k in curr_proj_pt and curr_proj_pt[k] > min_pts[player_type], player_years2))
#        player_years = player_years2

        ivars2[stat] = []
        depvars2[stat] = []
        ptvars[stat] = []
        for pyear in player_years:
            row = []
            for st in proj_stats:
                systems2 = list(filter(lambda s: not ((st in ['sv','saverate']) and s=='zips'),proj_systems))
                row.extend(projs[st][pyear][system] for system in systems2)
            ivars2[stat].append(row)
            if rmse_test:
                depvars2[stat].append(actuals[stat][pyear]['actual'])
                ptvars[stat].append(actualspt[pyear]['actual'])
     
        x = numpy.array(ivars2[stat])

        if rmse_test:
            y = numpy.array(depvars2[stat])
            pt = numpy.array(ptvars[stat])

        w = weight * variances[stat]

        #print x
        
        # Normalize the other stats used
        j = 0
        for st in proj_stats:
            systems2 = list(filter(lambda s: not ((st in ['sv','saverate']) and s=='zips'),proj_systems))
            if st == stat:
                xproj = x[:,j:j+len(systems2)]
            for system in systems2:
                if st != stat:
                    x[:,j] = standardize(x[:,j],w)
                j = j + 1

        
        #print x

        yrs =     get_year_var(player_years, proj_years)
        if no_yr_weight:
             yrs =  yrs / weight
             
        rookies = get_rookie_var(player_years, [curr_year], 'pecota', player_type, pm)
        ages =    get_age_var(player_years, [curr_year], 'pecota', player_type, pm, weight)

        aux = numpy.hstack((yrs, rookies, ages))
        aux2 = add_quad_interactions(aux)

        teams   = get_team_vars(player_years, [curr_year], 'pecota', player_type, pm)
        aux3 = numpy.hstack((aux2,teams))

        if old_model:
            x2 = get_final_regs(x,aux3,weight)
        else:
            x2 = get_final_regs(x,yrs,weight)
        
        final_stat_proj = models[stat].predict(x2)
        final_projs[stat] = dict(zip(player_years,final_stat_proj))


        systems = list(filter(lambda s: not ((stat in ['sv','saverate']) and s=='zips'),proj_systems))

        # Don't weight errors for playing-time variables
        if rmse_test:
            if st in ['pa','ab','g','gs','ip','sv']:
                pt = numpy.ones(y.shape)

            print()
            print("Final %s RMSE: %f" % (stat,getRMSE(final_stat_proj,y,pt)))

            j = 0
            for sys in systems:
                print("%s  %s RMSE: %f" % (sys, stat, getRMSE(xproj[:,j],y,pt)))
                j = j+1
            
        

        

    cols = ['fg_id','last_name','first_name','positions']
    cols.extend(stats[player_type])

    with open(csvfile, 'w') as f:

        writer = csv.DictWriter(f, cols)
        writer.writeheader()

        player_years.sort(key=lambda k: final_projs[playing_time][k])
        player_years.reverse()

        for k in player_years:
            row = {'fg_id': fg_ids[k] ,
                   'first_name': first_names[k],
                   'last_name': last_names[k],
                   'positions': positions[k],
                   }
            for stat in stats[player_type]:
                row[stat] = final_projs[stat][k]
            writer.writerow(row)

