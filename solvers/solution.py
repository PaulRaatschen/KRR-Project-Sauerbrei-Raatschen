from importlib.resources import path
from msilib.schema import Control
from typing import List, Dict, Union, Tuple, Callable
from clingo import Symbol, Control, Model, Number, Function
from math import inf
from os import path


WORKING_DIR : str = path.abspath(path.dirname(__file__))
ENCODING_DIR : str = path.join(WORKING_DIR,'encodings')
SAPF_FILE : str = path.join(ENCODING_DIR,'singleAgentPF_inc.lp')

class Plan: 

    def __init__(self,occurs : List[Symbol] = None, positions : List[Symbol] = None, constraints : List[Symbol] = None, cost : int = 0, goal : Symbol = None):
        self.occurs = occurs if occurs else []
        self.positions = positions if positions else []
        self.constraints = constraints if constraints else []
        self.cost = cost
        self.goal = goal

    def clear(self):
        self.occurs = []
        self.positions = []
        self.cost = 0

class Solution:

    def __init__(self,agents : List[int] = None,inits : List[Symbol] = None, instance_atoms : List[Symbol] = None, plans : Dict[int,Plan] = None, num_of_nodes : int = 0):
        self.agents = agents if agents else []
        self.inits = inits if inits else []
        self.instance_atoms = instance_atoms if instance_atoms else []
        self.plans = plans if plans else {}
        self.initial_plans : Dict[int,Plan] = {}
        self.num_of_nodes = num_of_nodes
        self.makespan : int = 0
        self.cost : int = 0
        self.execution_time : float = 0.0
        self.satisfied : bool = False

    def clear_plans(self) -> None:
        for plan in self.plans.values():
            plan.clear()


    def clear_plan(self,agent : int) -> None:
        self.plans[agent].clear()


    def save(self, filepath : str):
        with open(filepath, 'w', encoding='utf-8') as file:
            for init in self.inits:
                file.write(f"{init}. ")
            for plan in self.plans.values():
                for occur in plan.occurs:
                    file.write(f"{occur}. ")


    def get_initial_plans(self) -> List[Plan]:
        ctl : Control

        def model_parser(model : Model,agent : int) -> bool:
            for atom in model.symbols(shown=True):
                if atom.name == 'occurs':
                    self.initial_plans[agent].occurs.append(atom)
                elif atom.name == 'position' and atom.arguments[0].number == agent:
                    self.initial_plans[agent].positions.append(atom)
            return False

        if not self.initial_plans:
            for agent in self.agents:
                self.initial_plans[agent] = Plan(goal=self.plans[agent].goal)
                ctl = Control(arguments=['-Wnone',f'-c r={agent}']) 
                ctl.load(SAPF_FILE)

                with ctl.backend() as backend:
                    fact = backend.add_atom(self.initial_plans[agent].goal)
                    backend.add_rule([fact])
                    for atom in self.instance_atoms:
                        fact = backend.add_atom(atom)
                        backend.add_rule([fact])
                    
                self.initial_plans[agent].cost = self.incremental_solving(ctl,self.num_of_nodes,lambda m, a=agent : model_parser(m,a))

        return self.initial_plans
        

    def get_initial_plan_info(self) -> Dict[str,Union[List[Plan],int]]:
        result : Dict[str,Union[List[Plan],int]] = { 'plans' : {}, 'soc': 0, 'makespan' : 0 }
        soc : int = 0
        makespan : int = 0

        if not self.initial_plans:
            self.get_initial_plans()

        result['plans'] = self.initial_plans

        for plan in self.initial_plans.values():
            soc += plan.cost
            makespan = max(makespan,plan.cost)

        result['soc'] = soc
        result['makespan'] = makespan

        return result

    def get_soc(self) -> int:
        if self.cost > 0:
            return self.cost
        else:
            cost : int = 0
            for plan in self.plans.values():
                cost += plan.cost
            return cost


    def get_makespan(self) -> int:

        if self.makespan == 0:
            for plan in self.plans.values():
                self.makespan = max(self.makespan,plan.cost)

        return self.makespan

    def get_total_moves(self) -> int:
        total_moves : int = 0

        for plan in self.plans.values():
            total_moves += len(plan.occurs)

        return total_moves

    def get_norm_total_moves(self) -> float:
        if not self.initial_plans.values():
            self.get_initial_plans()
        
        total : int = 0

        for plan in self.initial_plans.values():
            total += len(plan.occurs)

        return self.get_total_moves() / total

    def get_norm_soc(self) -> float:
        info : Dict[str,Union[List[Plan],int]] = self.get_initial_plan_info()

        return self.get_soc() / info['soc']

    def get_norm_makespan(self) -> float:
        info : Dict[str,Union[List[Plan],int]] = self.get_initial_plan_info()

        return self.get_makespan() / info['makespan']
    
    def get_density(self) -> float:
        return len(self.agents) * 2 / (self.num_of_nodes)

    def save_initial_plans(self,filepath : str) -> None:

        if not self.initial_plans:
            self.get_initial_plans()

        with open(filepath,'w',encoding='utf-8') as file:
                for plan in self.initial_plans.values():
                    for atom in plan.occurs:
                        file.write(f'{atom}.\n')
        
    @staticmethod   
    def incremental_solving(ctl : Control, max_horizon : int, model_parser : Callable[[Model],bool]) -> int:

        ret, step = None, 0

        while((step < max_horizon) and (ret is None or (step < max_horizon and not ret.satisfiable))):
            parts = []
            parts.append(("check", [Number(step)]))
            if step > 0:
                ctl.release_external(Function("query", [Number(step - 1)]))
                parts.append(("step", [Number(step)]))
            else:
                parts.append(("base", []))
            ctl.ground(parts)
            ctl.assign_external(Function("query", [Number(step)]), True)
            ret, step = ctl.solve(on_model=model_parser), step + 1   

        return inf  if not ret or (not ret.satisfiable) else step - 1   
    
    

