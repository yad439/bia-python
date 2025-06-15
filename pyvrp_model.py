from collections.abc import Iterable
from pyvrp import Client, Depot, Model
from pyvrp.stop import MaxRuntime

from instance import Instance, dataclass

# Constant for converting float values to integers

def build_first_stage_model(instance:Instance):
	model=Model()
	depot = model.add_depot(x=instance.depot.x, y=instance.depot.y)
	model.add_vehicle_type(
		num_available=100,
		start_depot=depot,
		capacity=instance.vehicle_capacity,
		fixed_cost=instance.weights.vehicle_salary,
		max_duration=instance.vehicle_shift_size+instance.depot.load_time,
		unit_distance_cost=instance.weights.fuel_cost,
		reload_depots=[depot])
	clients=[model.add_client(
			x=order.x, y=order.y,
			delivery=order.volume,
			service_duration=order.vehicle_service_time,
			tw_early=order.time_window[0],
			tw_late=order.time_window[1],
			required=False if order.optional else True,
			prize=instance.weights.optional_order_penalty if order.optional else 0,
			name=str(order.id)
		) for order in instance.orders]
	# Add edges between depot and clients
	for i, client in enumerate(clients):
		model.add_edge(depot, client, distance=instance.distances[0][i+1], duration=instance.vehicle_times[0][i+1])
		model.add_edge(client, depot, distance=instance.distances[i+1][0], duration=(instance.vehicle_times[i+1][0]+instance.depot.load_time))

	# Add edges between clients
	for i, client1 in enumerate(clients):
		for j, client2 in enumerate(clients):
			if i != j:
				model.add_edge(client1, client2,
				    distance=int(instance.distances[i+1][j+1]),
					duration=int(instance.vehicle_times[i+1][j+1]),
					)
	return model

@dataclass
class VehicleRoute:
	clients: list[tuple[int,int]]
	distance:int
	shift_length: int

def detailed_route(instance:Instance, route:Iterable[Client|Depot], start_time:int):
	result:list[tuple[int,int]]= []
	time=start_time
	distance=0
	client_mapping = {client.id: client for client in instance.orders}
	prev_client=0
	for node in route:
		if isinstance(node, Depot):
			time+=instance.vehicle_times[prev_client][0]
			result.append((0,time))
			time+=instance.depot.load_time
		else:
			order = client_mapping[int(node.name)]
			time += instance.vehicle_times[prev_client][order.id]
			distance+= instance.distances[prev_client][order.id]
			assert time<= order.time_window[1]
			if time<order.time_window[0]:
				time = order.time_window[0]
			result.append((order.id, time))
			time += order.vehicle_service_time
			prev_client = order.id
	time+= instance.vehicle_times[prev_client][0]
	distance+= instance.distances[prev_client][0]
	assert time-start_time <= instance.vehicle_shift_size
	return VehicleRoute(result,distance,time-start_time)


def solve_first_stage_model(instance: Instance):
	model = build_first_stage_model(instance)
	solution = model.solve(stop=MaxRuntime(60))
	print(solution)
	routes=(detailed_route(instance,(model.locations[i] for i in route), route.start_time()) for route in solution.best.routes())
	return routes