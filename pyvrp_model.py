from collections.abc import Iterable

from pyvrp import Client, Depot, Model
from pyvrp.stop import MaxRuntime

from instance import Instance, dataclass


def build_first_stage_model(instance: Instance):
	"""
	Builds the PyVRP model for vehicles only based on the given instance.

	Args:
		instance (Instance): An object containing the problem instance data

	Returns:
		Model: A configured PyVRP model.
	"""
	model = Model()
	depot = model.add_depot(x=instance.depot.x, y=instance.depot.y)
	model.add_vehicle_type(num_available=len(instance.orders),
	                       start_depot=depot,
	                       capacity=instance.vehicle_capacity,
	                       fixed_cost=instance.weights.vehicle_salary,
	                       max_duration=instance.vehicle_shift_size + instance.depot.load_time,
	                       unit_distance_cost=instance.weights.fuel_cost,
	                       reload_depots=[depot])
	clients = [
	    model.add_client(x=order.x,
	                     y=order.y,
	                     delivery=order.volume,
	                     service_duration=order.vehicle_service_time,
	                     tw_early=order.time_window[0],
	                     tw_late=order.time_window[1],
	                     required=False if order.optional else True,
	                     prize=instance.weights.optional_order_penalty if order.optional else 0,
	                     name=str(order.id)) for order in instance.orders
	]
	# Add edges between depot and clients
	for i, client in enumerate(clients):
		model.add_edge(depot, client, distance=instance.distances[0][i + 1], duration=instance.vehicle_times[0][i + 1])
		model.add_edge(client,
		               depot,
		               distance=instance.distances[i + 1][0],
		               duration=(instance.vehicle_times[i + 1][0] + instance.depot.load_time))

	# Add edges between clients
	for i, client1 in enumerate(clients):
		for j, client2 in enumerate(clients):
			if i != j:
				model.add_edge(
				    client1,
				    client2,
				    distance=int(instance.distances[i + 1][j + 1]),
				    duration=int(instance.vehicle_times[i + 1][j + 1]),
				)
	return model


@dataclass
class VehicleRoute:
	"""A structure representing a vehicle route."""
	clients: list[tuple[int, int]]
	distance: int
	shift_length: int


def calculate_detailed_route(instance: Instance, route: Iterable[Client | Depot], start_time: int) -> VehicleRoute:
	"""
	Calculates a detailed route for a vehicle, including the sequence of stops,
	arrival times, total distance traveled, and total time spent.

	Args:
		instance (Instance): The problem instance containing data about clients,
			depots, distances, and vehicle constraints.
		route (Iterable[Client | Depot]): The sequence of nodes (clients and depots)
			that the vehicle will visit obdained from the PyVRP model.
		start_time (int): The starting time for the route.

	Returns:
		VehicleRoute: A description of the vehicle route.
	"""
	result: list[tuple[int, int]] = []
	time = start_time
	distance = 0
	# Create a mapping from client ID to client object for easy access
	client_mapping = {str(client.id): client for client in instance.orders}
	prev_client = 0
	for node in route:
		if isinstance(node, Depot):
			time += instance.vehicle_times[prev_client][0]
			result.append((0, time))
			time += instance.depot.load_time
		else:
			order = client_mapping[node.name]
			time += instance.vehicle_times[prev_client][order.inner_id]
			distance += instance.distances[prev_client][order.inner_id]

			# Check the time window constraints
			assert time <= order.time_window[1]
			if time < order.time_window[0]:
				time = order.time_window[0]

			result.append((order.id, time))
			time += order.vehicle_service_time
			prev_client = order.inner_id
	# Add the return to depot
	time += instance.vehicle_times[prev_client][0]
	distance += instance.distances[prev_client][0]
	assert time - start_time <= instance.vehicle_shift_size
	return VehicleRoute(result, distance, time - start_time)


def build_vehicle_schedule(instance: Instance, time_limit: float):
	"""
	Build and solves the PyVRP model for the routing problem of vehicles only.

	Args:
		instance (Instance): The problem instance containing all necessary data for the model.
		time_limit (float): The maximum allowed runtime for solving the model, in seconds.

	Returns:
		list[VehicleRoute]: A a list of `VehicleRoute` objects, each representing a route in a best-found solution.
	"""
	model = build_first_stage_model(instance)
	solution = model.solve(stop=MaxRuntime(time_limit), seed=43)
	routes = [
	    calculate_detailed_route(instance, (model.locations[i]
	                                        for i in route), route.start_time())
	    for route in solution.best.routes()
	]
	return routes
