import json
from typing import Any
from loader_schedule import LoaderAssignment
from instance import Instance


def export_solution_to_json(instance: Instance, vehicle_routes: list[list[tuple[int, int]]], loader_schedules: list[list[LoaderAssignment]], output_path: str):
    vehicles: list[dict[str, Any]] = []
    for idx, route in enumerate(vehicle_routes):
        route_ids = [order_id for order_id, _ in route]
        times = [arr_time/100 for order_id, arr_time in route if order_id != 0]
        if route_ids[0] != 0:
            route_ids = [0] + route_ids
        if route_ids[-1] != 0:
            route_ids = route_ids + [0]
        vehicles.append({
            "id": idx + 1,
            "route": route_ids,
            "time": times
        })

    loaders: list[dict[str, Any]] = []
    for idx, schedule in enumerate(loader_schedules):
        loaders.append({
            "id": idx + 1,
            "route": [assignment.order_id for assignment in schedule]
        })

    solution = {
        "vehicles": vehicles,
        "loaders": loaders
    }
    with open(output_path, "w") as f:
        json.dump(solution, f, indent=4)
