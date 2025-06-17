import json
from pathlib import Path

from instance import Instance
from loader_schedule import LoaderAssignment, LoaderJob
import objective
from pyvrp_model import VehicleRoute
import math

def build_route(instance:Instance, route: list[int],times:list[float]):
    start_time = int(times[0]*100+0.5)-instance.vehicle_times[0][route[1]]
    time= start_time
    distance=0
    prev=0
    i=0
    for node in route[1:-1]:
        if node>0:
            order = instance.orders[node-1]
            time += instance.vehicle_times[prev][order.inner_id]
            distance += instance.distances[prev][order.inner_id]
            assert time <= order.time_window[1]
            if time < order.time_window[0]:
                time = order.time_window[0]
            #assert time==int(times[i]*100), f'{time} {times[i]*100}'
            time += order.vehicle_service_time
            prev = order.inner_id
        else:
            time += instance.vehicle_times[prev][0]
            #assert time == int(times[i]*100), f'{time} {times[i]*100}'
            time += instance.depot.load_time
            prev = 0
        i+=1
    time += instance.vehicle_times[prev][0]
    distance += instance.distances[prev][0]
    assert time-start_time <= instance.vehicle_shift_size
    return VehicleRoute(list(zip(route[1:-1],(int(t*100+0.5) for t in times))),distance,time-start_time)

def build_loader(instance: Instance, route: list[int], jobs: list[LoaderJob]):
    start_time = jobs[0].earliest_time
    time = start_time
    prev = 0
    i = 0
    result = []
    for node in route:
        job=next(j for j in jobs if j.order.inner_id == node)
        time+=instance.loader_times[prev][job.order.inner_id]

def buildLoader2(instance: Instance, route: list[int],veh_t:dict[int,int]):
    stn=route[0]
    een= route[-1]
    start=veh_t[stn]
    end=veh_t[een]
    end+=instance.loader_times[een][stn]
    return LoaderAssignment(route,end-start)

def read_enc(instance_p:str,file:str,out):
    instance=Instance.from_json(instance_p)
    with open(file, 'r') as f:
        data=json.load(f)
    vr=[build_route(instance, r['route'], r['time']) for r in data['vehicles']]
    mp={n:int(t*100+0.5) for r in data['vehicles'] for n,t in zip(r['route'][1:-1],r['time'])}
    lr=[buildLoader2(instance, r['route'], mp) for r in data['loaders']]
    o1=objective.calculate_vehicle_objective(instance, vr)
    o2=objective.calculate_loader_objective(instance, lr)
    o3=objective.calculate_loader_objective_wrong(instance, lr)
    print(o1/10000,o2/10000,o3/10000)
    print(Path(instance_p).stem,round_((o1+o2)/10000),round_((o1+o3)/10000),sep=',',file=out)

def round_(x:float):
    return math.floor(x * 100 + 0.5) /100

with open('res.csv', 'w') as out:
    print('instance,objective_corrected,objective_validator', file=out)
    for i in range(1, 11):
        read_enc(f'instances/i{i}.json', f'8/sol_i{i}.json', out)
