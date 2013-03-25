from projections import *
from sklearn.linear_model import LassoLarsCV
import numpy
import random

#base_dir = "C:\\Users\\bhebert\\Dropbox\\Baseball\\CSVs for DB"
base_dir = "~/Dropbox/Baseball/CSVs for DB"

pm = MyProjectionManager('sqlite:///projections.db')
#pm.read_everything_csv(base_dir = base_dir)

stats = ['obp', 'slg', 'r', 'rbi', 'sb']
wstat = 'pa'
num_projs = 3
min_weight = 400
years = [2011, 2012, 2013]

ivars = {}
depvars = {}
weights = {}
projids = {}
projvars = {}

for stat in stats:
    ivars[stat] = []
    depvars[stat] = []
    weights[stat] = []
    projids[stat] = []
    projvars[stat] = []

for year in years:
    players = pm.batter_projection_groups(filter_clause=ProjectionSystem.year==year)

    for player, pairs in players:

        projs = {}
        depvar = {}
        weight = {}
        for stat in stats:
            projs[stat] = [-1, -1, -1]
            depvar[stat] = -1
            weight[stat] = -1

        for (_, projection) in pairs:
            sys = projection.projection_system

            for stat in stats:
                if sys.is_actual:
                    depvar[stat] = getattr(projection,stat)
                    weight[stat] = getattr(projection,wstat)
                elif sys.name == 'pecota' :
                    projs[stat][0] = getattr(projection,stat)
                elif sys.name == 'zips' :
                    projs[stat][1] = getattr(projection,stat)
                elif sys.name == 'steamer' :
                    projs[stat][2] = getattr(projection,stat)
        
        for stat in stats:
            if min(projs[stat]) > 0:

                if year < 2013 and weight > min_weight:
                    ivars[stat].append(projs[stat])
                    depvars[stat].append(depvar[stat])
                    weights[stat].append(weight[stat])
                elif year == 2013:
                    projvars[stat].append(projs[stat])
                    projids[stat].append(player.mlb_id)


models = {}
final_projs = {}

for stat in stats:

    models[stat] = LassoLarsCV(cv=20)
    combined = zip(ivars[stat], depvars[stat])
    random.shuffle(combined)

    ivars[stat][:], depvars[stat][:] = zip(*combined)

    x = numpy.array(ivars[stat])
    y = numpy.array(depvars[stat])
    x2 = numpy.array(projvars[stat])

    models[stat].fit(x,y)

    print stat
    print models[stat].coef_
    print models[stat].intercept_

    final_projs[stat] = models[stat].predict(x2)
