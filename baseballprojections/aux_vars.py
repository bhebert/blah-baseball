import datetime
import numpy
import baseballprojections.projectionmanager
from baseballprojections.helper import valid_teams

def get_year_var(player_years,proj_years):
    
    dummies = []
    for pyear in player_years:
        vals = pyear.split("_")
        row = []
        for year in proj_years[0:-1]:
            if int(vals[1]) <= year:
                dummy = 1
            else:
                dummy = 0
            row.extend([dummy])
        dummies.append(row)
    
    return numpy.array(dummies)

def get_team_vars(player_years, proj_years, system, player_type, pm):
    
    data = pm.get_player_year_data(proj_years, [system],
                                   player_type, ['team'],
                                   {'team': None })['team']
    dummies = []
    # drop the last valid team 'FA' to avoid LD
    vteams = valid_teams[2:]
    for pyear in player_years:
        if pyear in data:
            dummies.append(list(map(lambda x: 1 if x == data[pyear][system] else 0, 
                               vteams)))
        else:
            dummies.append([0] * len(vteams))
    return numpy.array(dummies)

def get_rookie_var(player_years, proj_years, system, player_type,pm):
    
    rookies = pm.get_player_year_data(proj_years, [system],
                                         player_type, ['rookie'],
                                         {'rookie':None})['rookie']
    dummies = []
    for pyear in player_years:
        if pyear in rookies:
            dummies.append([rookies[pyear][system]])
        else:
            dummies.append([0])
    return numpy.array(dummies)


# from 1 Apr, arbitrarily
def stat_age(p, player_type):
    age_date = datetime.date(p.projection_system.year, 4, 1)
    if player_type == 'batter':
        birthdate = p.batter.birthdate
    else:
        birthdate = p.pitcher.birthdate
    if birthdate is not None:
        age = age_date - birthdate
        return age.days / 365.25
    else:
        return None


def get_age_var(player_years, proj_years, system, player_type, pm, weight):

    stat_functions = {
        'age': lambda p: stat_age(p, player_type)
    }
    data = pm.get_player_year_data(proj_years, [system],
                                   player_type, ['age'],
                                   stat_functions)['age']
    ages = []
    for pyear in player_years:
        if pyear in data:
            ages.append([data[pyear][system]])
        else:
            # if you have time get the missing ones in there
            ages.append([0])

    ages1 = numpy.array(ages)
    ages1[:,0] = standardize(ages1[:,0],weight)
    return ages1

def standardize(vec, weight):
    vecvar = numpy.std(vec)
    vecmean = numpy.mean(vec)
    return (vec - vecmean) / vecvar * weight

def getRMSE(act,proj,weight):
    act2 = act - numpy.mean(act) - proj + numpy.mean(proj)
    return numpy.sqrt(numpy.sum(numpy.multiply(numpy.multiply(act2,act2),weight))/numpy.sum(weight))
    
# aux/interaction helpers

def add_quad_interactions(aux):
    quads = []
    for row in aux:
        row2 = []
        for i in range(0,len(row)):
            for j in range(i+1,len(row)):
                val = row[i]*row[j]
                row2.extend([val])
        quads.append(row2)

    xquads = numpy.array(quads)    
    return numpy.hstack((aux, xquads))

def get_final_regs(x,aux, weight):
    regs = []
    xstand = numpy.copy(x)
    for j  in range(0,len(x[0])):
        xstand[:,j] = standardize(x[:,j],weight)
    for i in range(0,len(x)):
        rowx = x[i]
        rowxn = xstand[i]
        row2 = []
        rowaux = aux[i]
        rowaux_x = []
        for j in range(0,len(rowx)):
            for k in range(j,len(rowx)):
                val = rowx[j]*rowxn[k]
                row2.extend([val])
            for k  in range(0,len(rowaux)):
                rowaux_x.extend([rowxn[j]*rowaux[k]])
        row2.extend(rowaux_x)
        regs.append(row2)
        
    xregs = numpy.array(regs)
    auxw = aux * weight
    return numpy.hstack((x,auxw, xregs))
    #return numpy.hstack((x,xregs))
