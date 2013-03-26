from projections import *
from sklearn.linear_model import LassoLarsCV
import numpy
import numpy.ma
import random
import csv

base_dir = "C:\\Users\\Benjamin\\Dropbox\\Baseball\\CSVs for DB"
#base_dir = "/Users/andrew_lim/Dropbox/Baseball/CSVs for DB"
csvfile = "HitterProjs.csv"

pm = MyProjectionManager('sqlite:///projections.db')
#pm = MyProjectionManager()
#pm.read_everything_csv(base_dir = base_dir)

player_type = 'batter'
playing_time = 'pa'
stats = ['pa', 'ab', 'obp', 'slg','sb', 'cs', 'r', 'rbi']
proj_systems = ['pecota', 'zips', 'steamer']

cv_num = 20
min_pt = 300

proj_years = [2011, 2012]
curr_year = 2013

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
            positions[key] = getattr(projection,'positions')


# This makes a model for choosing the sample    

pt_projs = pm.get_player_year_data(proj_years, proj_systems,
                                   player_type, playing_time)
pt_actuals = pm.get_player_year_data(proj_years, ['actual'],
                                     player_type, playing_time)
#pt_projs = pm.get_proj_data(proj_years,player_type,playing_time)
#pt_actuals = pm.get_actual_data(proj_years,player_type,playing_time)

player_years = list(set(pt_actuals.keys()) & set(pt_projs.keys()))
random.shuffle(player_years)

ivars = []
depvars = []

for pyear in player_years:
    ivars.append([pt_projs[pyear][system] for system in proj_systems])
    depvars.append(pt_actuals[pyear]['actual'])
    #ivars.append(pt_projs[pyear])
    #depvars.append(pt_actuals[pyear])

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

for stat in stats:

    projs = pm.get_player_year_data(proj_years, proj_systems,
                                    player_type, playing_time)
    actuals = pm.get_player_year_data(proj_years, proj_systems,
                                      player_type, playing_time)
    #projs = pm.get_proj_data(proj_years,player_type,stat)
    #actuals = pm.get_actual_data(proj_years,player_type,stat)

    player_years = list(set(actuals.keys()) & set(projs.keys()))

    fp_years = filter(lambda k: k in sample_proj_pt and sample_proj_pt[k] > min_pt, player_years)
    
    random.shuffle(fp_years)

    ivars[stat] = []
    depvars[stat] = []

    for pyear in fp_years:
        ivars[stat].append([pt_projs[pyear][system] for system in proj_systems])
        depvars[stat].append(pt_actuals[pyear]['actual'])
        #ivars[stat].append(projs[pyear])
        #depvars[stat].append(actuals[pyear])

    x = numpy.array(ivars[stat])
    y = numpy.array(depvars[stat])

    models[stat] = LassoLarsCV(cv=cv_num)
    models[stat].fit(x,y)

    print "Model for " + stat
    print "Num of player-seasons in sample: " + str(len(fp_years))
    print models[stat].coef_
    print models[stat].intercept_

ivars2 = {}

for stat in stats:
    
    projs = pm.get_player_year_data([curr_year], proj_systems, 
                                    player_type, stat)
    #projs = pm.get_proj_data([curr_year],player_type,stat)

    player_years = projs.keys()

    ivars2[stat] = []

    for pyear in player_years:
        ivars2[stat].append([projs[pyear][system] for system in proj_systems])
        #ivars2[stat].append(projs[pyear])
 
    x = numpy.array(ivars2[stat])

    final_stat_proj = models[stat].predict(x)

    final_projs[stat] = dict(zip(player_years,final_stat_proj))

cols = ['mlb_id','last_name','first_name','positions']
cols.extend(stats)

#with open(csvfile, 'wb') as f:
with open(csvfile, 'w') as f:
    writer = csv.DictWriter(f, cols)
    writer.writeheader()

    for k in player_years:
        row = {'mlb_id': mlb_ids[k] ,
               'first_name': first_names[k],
               'last_name': last_names[k],
               'positions': positions[k],
               }
        for stat in stats:
            row[stat] = final_projs[stat][k]
        writer.writerow(row)
                
    
