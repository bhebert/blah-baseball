import datetime
import numpy
import baseballprojections.projectionmanager
from baseballprojections.schema import Player
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

def get_rookie_var(player_years, proj_years, systems, player_type,pm):
    
    rookies = pm.get_player_year_data(proj_years, systems,
                                         player_type, ['rookie'],
                                         {'rookie':None},True)['rookie']
    dummies = []
    for pyear in player_years:
        rdummy = None
        for sys in systems:
            if rookies[pyear][sys] is not None and rdummy is None:
                rdummy = rookies[pyear][sys]
            elif rookies[pyear][sys] is not None and rookies[pyear][sys] != rdummy:
                print('Warning: rookie status differs by system')
                print(pyear)
        if rdummy is not None:
            dummies.append([rdummy])
        else:
            print('Warning: rookie status not found')
            print(pyear)
            dummies.append([0])
    return numpy.array(dummies)


# from 1 Apr, arbitrarily
def stat_age(p,year):
    age_date = datetime.date(year, 4, 1)
    birthdate = p.birthdate
    
    if birthdate is not None:
        age = age_date - birthdate
        return age.days / 365.25
    else:
        return None

# I have kept unnecessary arguments to maintain the 2013 version of the code
def get_age_var(player_years, proj_years, system, player_type, pm, weight):


    all_players = pm.query(Player).all()    
 
    ages = []
    for pyear in player_years:
        vals = pyear.split('_')

        players = filter(lambda p: p.fg_id == vals[0], all_players)
        age = stat_age(next(players),int(vals[1]))
        
        if age is not None:
            ages.append([age])
        else:
            # if you have time get the missing ones in there
            print('Warning: missing age')
            print(pyear)
            ages.append([0])

    ages1 = numpy.array(ages)
    if weight > 0:
        ages1[:,0] = standardize(ages1[:,0],weight)
    return ages1

def get_dc_var(player_years,proj_years,player_type,pm):
    stat_functions = {
        'dc_dummy': lambda p: p.dc_fl is not None and p.dc_fl == 'T'
    }
    data = pm.get_player_year_data(proj_years, ['pecota'],
                                   player_type, ['dc_dummy'],
                                   stat_functions)['dc_dummy']
    dcs = []
    for pyear in player_years:
        if pyear in data:
            dcs.append([data[pyear]['pecota']])
        else:
            print('Warning: dc flag missing')
            print(pyear)
            dcs.append([0])
    return dcs

def standardize(vec, weight):
    vecvar = numpy.std(vec)
    if vecvar > 0:
        vecmean = numpy.mean(vec)
        return (vec - vecmean) / vecvar * weight
    else:
        return vec

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

def get_final_regs(x,aux, weight,x2=True):
    regs = []
    xstand = numpy.copy(x)
    for j  in range(0,len(x[0])):
        if weight > 0:
            xstand[:,j] = standardize(x[:,j],weight)
        else:
            xstand[:,j] = x[:,j]
    for i in range(0,len(x)):
        rowx = x[i]
        rowxn = xstand[i]
        row2 = []
        rowaux = aux[i]
        rowaux_x = []
        for j in range(0,len(rowx)):
            if x2:
                for k in range(j,len(rowx)):
                    val = rowx[j]*rowxn[k]
                    row2.extend([val])
            for k  in range(0,len(rowaux)):
                rowaux_x.extend([rowxn[j]*rowaux[k]])
        row2.extend(rowaux_x)
        regs.append(row2)
        
    xregs = numpy.array(regs)
    if weight > 0:
        auxw = aux * weight
    else:
        auxw = aux
    return numpy.hstack((x,auxw, xregs))
    #return numpy.hstack((x,xregs))
