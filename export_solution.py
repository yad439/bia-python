import json
from collections.abc import Iterable
from typing import Any

from loader_schedule import LoaderRoute
from pyvrp_model import VehicleRoute


def export_solution_to_json(vehicle_routes: Iterable[VehicleRoute], loader_schedules: Iterable[LoaderRoute],
                            output_path: str):
	"""
Export the solution to a JSON file.

This function takes the found vehicle and loader routes and saves them in a specified JSON format.

Args:
        instance (Instance): The problem instance containing all relevant data.
        vehicle_routes (list[VehicleRoute]): List of vehicle routes where each route contains a sequence of clients
        loader_schedules (list[LoaderAssignment]): List of loader assignments where each assignment contains a sequence
        output_path (str): The file path where the JSON solution will be saved.
"""
	vehicles: list[dict[str, Any]] = []
	for idx, route in enumerate(vehicle_routes):
		route_ids = [order_id for order_id, _ in route.clients]
		times = [arr_time / 100 for order_id, arr_time in route.clients if order_id != 0
		        ]  # Divide by 100 to get original values
		if route_ids[0] != 0:
			route_ids = [0] + route_ids
		if route_ids[-1] != 0:
			route_ids = route_ids + [0]
		vehicles.append({"id": idx + 1, "route": route_ids, "time": times})

	loaders: list[dict[str, Any]] = []
	for idx, schedule in enumerate(loader_schedules):
		loaders.append({"id": idx + 1, "route": [assignment for assignment in schedule.order_ids]})

	solution = {"vehicles": vehicles, "loaders": loaders}
	with open(output_path, "w") as f:
		json.dump(solution, f, indent=4)
