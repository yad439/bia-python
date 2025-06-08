from dataclasses import dataclass
import math
import json


@dataclass
class Depot:
    x: int
    y: int
    load_time: float


@dataclass
class Order:
    id: int
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
    vehicle_salary: int
    loader_salary: int
    fuel_cost: float
    loader_work: float
    optional_order_penalty: int


@dataclass
class Instance:
    vehicle_capacity: int
    vehicle_speed: float
    loader_speed: float
    vehicle_shift_size: int
    loader_shift_size: int
    depot: Depot
    orders: list[Order]
    weights: Weights
    distances:list[list[float]]
    vehicle_times:list[list[float]]
    loader_times:list[list[float]]

    @classmethod
    def from_json(cls, json_path: str) -> 'Instance':
        """Load an instance from a JSON file."""
        with open(json_path, 'r') as f:
            data = json.load(f)

        depot = Depot(**data['depot'])
        orders = [Order(**order) for order in data['orders']]
        weights = Weights(**data['weights'])
        ditances:list[list[float]]=[]
        row=[0.0]
        for order in orders:
            row.append(strict_round(math.sqrt((depot.x - order.x) ** 2 + (depot.y - order.y) ** 2),2))
        ditances.append(row)
        for order1 in orders:
            row= [strict_round(math.sqrt((depot.x - order1.x) ** 2 + (depot.y - order1.y) ** 2),2)]
            row += [strict_round(math.sqrt((order1.x - order2.x) ** 2 + (order1.y - order2.y) ** 2),2) for order2 in orders]
            ditances.append(row)
        # Calculate vehicle_times and load_times
        vehicle_times = [[strict_round(distance / data['vehicle_speed'], 2) for distance in row] for row in ditances]
        loader_times = [[strict_round(distance / data['loader_speed'], 2) for distance in row] for row in ditances]

        return cls(
            vehicle_capacity=data['vehicle_capacity'],
            vehicle_speed=data['vehicle_speed'],
            loader_speed=data['loader_speed'],
            vehicle_shift_size=data['vehicle_shift_size'],
            loader_shift_size=data['loader_shift_size'],
            depot=depot,
            orders=orders,
            weights=weights,
            distances=ditances,
            vehicle_times=vehicle_times,
            loader_times=loader_times
        )

def strict_round(nums: float, accuracy: int = 0) ->  float:
    if accuracy == 0:
        return math.floor(nums + 0.5)
    else:
        multiplier = 10 ** accuracy
        return math.floor(nums * multiplier) / multiplier

# Example usage
if __name__ == "__main__":
    # Load the instance from the JSON file
    instance = Instance.from_json("/workspaces/bia-python/t1.json")
    print(f"Loaded instance with {len(instance.orders)} orders")
    print(f"Vehicle capacity: {instance.vehicle_capacity}")
    print(f"Depot location: ({instance.depot.x}, {instance.depot.y})")
