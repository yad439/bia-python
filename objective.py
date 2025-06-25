from collections.abc import Iterable

from instance import Instance
from loader_schedule import LoaderRoute
from pyvrp_model import VehicleRoute


def calculate_vehicle_objective(instance: Instance, vehicle_routes: Iterable[VehicleRoute]):
	"""
	Calculate the objective value for vehicle routes.
	The value is 10'000 times the total cost of the routes from the original formulation, which includes fuel cost and
	vehicle salary.

	Args:
		instance: The instance containing problem data.
		vehicle_routes: The vehicle routes to evaluate.
	"""
	routes_cost = sum(
	    route.distance * instance.weights.fuel_cost + instance.weights.vehicle_salary for route in vehicle_routes)
	all_orders = frozenset(client for route in vehicle_routes for client, _ in route.clients)
	penalty = 0
	for order in instance.orders:
		if order.optional and order.id not in all_orders:
			penalty += instance.weights.optional_order_penalty
	print(routes_cost / 10000, penalty / 10000)
	return routes_cost + penalty


def calculate_loader_objective(instance: Instance, loader_schedules: Iterable[LoaderRoute]):
	"""
	Calculate the objective value for loader schedules.
	The value is 10'000 times the total cost of the schedules from the original formulation, which includes loader work
	and loader salary. This function calculates the corrected value of the values

	Args:
		instance: The instance containing problem data.
		loader_routes: The loader routes to evaluate.
	"""
	return sum(schedule.shift_length * instance.weights.loader_work + instance.weights.loader_salary
	           for schedule in loader_schedules)


def calculate_loader_objective_wrong(instance: Instance, loader_routes: Iterable[LoaderRoute]):
	"""
	Calculate the objective value for loader schedules.
	The value is 10'000 times the total cost of the schedules from the original formulation, which includes loader work
	and loader salary. This function calculates the same value as the provided validator.

	Args:
		instance: The instance containing problem data.
		loader_routes: The loader routes to evaluate.
	"""
	return sum(instance.orders[schedule.order_ids[0] - 1].loader_service_time * instance.weights.loader_work +
	           instance.weights.loader_salary for schedule in loader_routes)
