from argparse import ArgumentParser
from asyncio.windows_events import NULL
from os import path
import os
import sys
import pandas as pd
import prioritized_planning
import sequential_planning
import cbs_solver
from solution import Solution

sys.path.append('../InstanceGenerator')
import GenerateInstance


def saveInstanceInfo(Name,solution):
    xSize = 0
    ySize = 0
    nodecount = 0
    for atom in solution.inits:
        if atom.arguments[0].arguments[0].name=='node':
            nodecount += 1
            if xSize < atom.arguments[1].arguments[1].arguments[0].number: xSize = atom.arguments[1].arguments[1].arguments[0].number
            if ySize < atom.arguments[1].arguments[1].arguments[1].number: ySize = atom.arguments[1].arguments[1].arguments[1].number
        

    instance = pd.DataFrame({'instance': [Name],'Xsize':xSize,'Ysize':ySize,'blocked_nodes': xSize*ySize-nodecount, 'number_of_agents': len(solution.agents)})
    instance.to_csv('instance.csv', mode='a', index=False, header = not os.path.exists('instance.csv'))



parser : ArgumentParser = ArgumentParser()
parser.add_argument("instance", type=str)
parser.add_argument("-tag", type=int,default = 0)
parser.add_argument("-gi", "--GenerateInstance", default=False, action="store_true")
args = parser.parse_args()
instanceName = path.basename(args.instance)

if(args.GenerateInstance == False):

    print("PrioritizedPlanning-Start")

    ppSolution = prioritized_planning.PrioritizedPlanningSolver(args.instance,False,False,10,NULL).solve()
    ppdf = pd.DataFrame({'instance': [instanceName],'tag':[args.tag],'solver':["PP"],'max_horizon': [ppSolution.max_horizon],'cost' : [ppSolution.cost],'exec_time' : [ppSolution.execution_time],'satisfied' : [ppSolution.satisfied]})
    ppdf.to_csv('results.csv', mode='a', index=False, header = not os.path.exists('results.csv'))

    saveInstanceInfo(instanceName,ppSolution)

    print("SequentialPlanning-Start")
    spSolution = sequential_planning.benchmark(args.instance).result
    spdf = pd.DataFrame({'instance': [instanceName],'tag':[args.tag],'solver':["SP"],'max_horizon': [spSolution.max_horizon],'cost' : [spSolution.cost],'exec_time' : [spSolution.execution_time],'satisfied' : [spSolution.satisfied]})
    spdf.to_csv('results.csv', mode='a', index=False, header = False)


    print("CBS-Start")
    cbsSolution = cbs_solver.CBS_Solver(args.instance,False,NULL).solve()
    cbsdf = pd.DataFrame({'instance': [instanceName],'tag':[args.tag],'solver':["CBS"],'max_horizon': [cbsSolution.max_horizon],'cost' : [cbsSolution.cost],'exec_time' : [cbsSolution.execution_time],'satisfied' : [cbsSolution.satisfied]})
    cbsdf.to_csv('results.csv', mode='a', index=False, header = False)

else:
    for i in range(1,5):
        modinstanceName = instanceName + str(i)
        GenerateInstance.createInstance(5 + 5*i,5*i,5 + 5*i,0)
        print("PrioritizedPlanning-Start")

        ppSolution = prioritized_planning.PrioritizedPlanningSolver(args.instance,False,False,10,NULL).solve()
        ppdf = pd.DataFrame({'instance': [modinstanceName],'tag':[args.tag],'solver':["PP"],'max_horizon': [ppSolution.max_horizon],'cost' : [ppSolution.cost],'exec_time' : [ppSolution.execution_time],'satisfied' : [ppSolution.satisfied]})
        ppdf.to_csv('results.csv', mode='a', index=False, header = not os.path.exists('results.csv'))
        saveInstanceInfo(modinstanceName,ppSolution)

        print("SequentialPlanning-Start")
        spSolution = sequential_planning.benchmark(args.instance).result
        spdf = pd.DataFrame({'instance': [modinstanceName],'tag':[args.tag],'solver':["SP"],'max_horizon': [spSolution.max_horizon],'cost' : [spSolution.cost],'exec_time' : [spSolution.execution_time],'satisfied' : [spSolution.satisfied]})
        spdf.to_csv('results.csv', mode='a', index=False, header = False)

        print("CBS-Start")
        cbsSolution = cbs_solver.CBS_Solver(args.instance,False,NULL).solve()
        cbsdf = pd.DataFrame({'instance': [modinstanceName],'tag':[args.tag],'solver':["CBS"],'max_horizon': [cbsSolution.max_horizon],'cost' : [cbsSolution.cost],'exec_time' : [cbsSolution.execution_time],'satisfied' : [cbsSolution.satisfied]})
        cbsdf.to_csv('results.csv', mode='a', index=False, header = False)
