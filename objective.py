from collections.abc import Iterable

from loader_schedule import LoaderAssignment

from pyvrp_model import VehicleRoute
from instance import Instance


def calculate_vehicle_objective(instance:Instance,vehicle_routes:Iterable[VehicleRoute]):
	total= sum(
		route.distance * instance.weights.fuel_cost + instance.weights.vehicle_salary
		for route in vehicle_routes
	)
	all_orders=frozenset(client for route in vehicle_routes for client, _ in route.clients)
	penalty=0
	for order in instance.orders:
		if order.optional and order.id not in all_orders:
			penalty += instance.weights.optional_order_penalty
	print(total/10000,penalty/10000)
	return total + penalty
def calculate_loader_objective(instance:Instance, loader_schedules:Iterable[LoaderAssignment]):
	return sum(
		schedule.shift_length * instance.weights.loader_work
		+ instance.weights.loader_salary
		for schedule in loader_schedules
	)
def calculate_loader_objective_wrong(instance:Instance, loader_schedules:Iterable[LoaderAssignment]):
	print(sum(instance.orders[schedule.order_ids[0]-1].loader_service_time for schedule in loader_schedules)/100,instance.weights.loader_work/100)
	print(len(loader_schedules),instance.weights.loader_salary/10_000)
	return sum(
		instance.orders[schedule.order_ids[0]-1].loader_service_time * instance.weights.loader_work
		+ instance.weights.loader_salary
		for schedule in loader_schedules
	)