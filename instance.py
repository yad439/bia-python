import json
import math
from dataclasses import dataclass


@dataclass
class Depot:
	"""A structure representing the depot of the problem instance. Load time is multipled by 100 to avoid floating-point
	precision issues."""
	x: int
	y: int
	load_time: int


@dataclass
class Order:
	"""A structure representing an order in the problem instance. Times are multiplied by 100 to avoid floating-point
	precision issues."""
	id: int
	inner_id: int  # Consecutive ID starting from 1, used for internal processing
	x: int
	y: int
	volume: int
	time_window: list[int]
	vehicle_service_time: int
	loader_cnt: int
	loader_service_time: int
	optional: int  # 0 or 1


@dataclass
class Weights:
	"""A structure representing the weights used in the problem instance. Values are multipleid by appropriate factors
	to avoid floating-point precision issues."""
	vehicle_salary: int
	loader_salary: int
	fuel_cost: int
	loader_work: int
	optional_order_penalty: int


@dataclass
class Instance:
	"""A structure representing the instance of the problem. Floating-point values are multiplied by 100 and rounded to
	integers to avoid floating-point precision issues."""
	vehicle_capacity: int
	vehicle_speed: float
	loader_speed: float
	vehicle_shift_size: int
	loader_shift_size: int
	depot: Depot
	orders: list[Order]
	weights: Weights
	distances: list[list[int]]
	vehicle_times: list[list[int]]
	loader_times: list[list[int]]

	@classmethod
	def from_json(cls, json_path: str):
		"""Load an instance from a JSON file."""
		with open(json_path, 'r') as f:
			data = json.load(f)

		data['depot']['load_time'] = integer_round(data['depot']['load_time'])
		depot = Depot(**data['depot'])

		# Process orders and multiply times to match rounding
		processed_orders: list[Order] = []
		i = 1
		for order_data in data['orders']:
			order_data['time_window'] = [t * 100 for t in order_data['time_window']]
			order_data['vehicle_service_time'] = order_data['vehicle_service_time'] * 100
			order_data['loader_service_time'] = order_data['loader_service_time'] * 100
			processed_orders.append(Order(**order_data, inner_id=i))
			i += 1

		orders: list[Order] = processed_orders
		weights = Weights(**data['weights'])
		weights.fuel_cost = integer_round(weights.fuel_cost)
		weights.loader_work = integer_round(weights.loader_work)
		# Weights are additionnally multiplied by 100 because they are proportional to square of distance
		weights.optional_order_penalty = integer_round(weights.optional_order_penalty) * 100
		weights.vehicle_salary = integer_round(weights.vehicle_salary) * 100
		weights.loader_salary = integer_round(weights.loader_salary) * 100
		distances: list[list[int]] = []
		row = [0]
		for order in orders:
			row.append(integer_round(math.sqrt((depot.x - order.x)**2 + (depot.y - order.y)**2)))
		distances.append(row)
		for order1 in orders:
			row = [integer_round(math.sqrt((depot.x - order1.x)**2 + (depot.y - order1.y)**2))]
			row += [integer_round(math.sqrt((order1.x - order2.x)**2 + (order1.y - order2.y)**2)) for order2 in orders]
			distances.append(row)
		# Calculate vehicle_times and load_times
		vehicle_times = [
		    [integer_round(distance / data['vehicle_speed'] / 100) for distance in row] for row in distances
		]
		loader_times = [[integer_round(distance / data['loader_speed'] / 100) for distance in row] for row in distances]

		return cls(vehicle_capacity=data['vehicle_capacity'],
		           vehicle_speed=data['vehicle_speed'],
		           loader_speed=data['loader_speed'],
		           vehicle_shift_size=data['vehicle_shift_size'] * 100,
		           loader_shift_size=data['loader_shift_size'] * 100,
		           depot=depot,
		           orders=orders,
		           weights=weights,
		           distances=distances,
		           vehicle_times=vehicle_times,
		           loader_times=loader_times)


def integer_round(nums: float):
	return int(math.floor(nums * 100 + 0.5))
