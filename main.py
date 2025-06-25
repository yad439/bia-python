import math
import argparse
from collections.abc import Iterable
from pathlib import Path

import export_solution
import loader_heuristic
import loader_schedule
import objective
import pyvrp_model
from instance import Instance
from loader_schedule import LoaderJob, LoaderRoute
from pyvrp_model import VehicleRoute


def generate_loader_schedules(instance: Instance, loader_jobs: list[LoaderJob], time_limit: float):
	"""Generates different variants of loader schedules."""
	loader_jobs.sort(key=lambda job: job.earliest_time)
	# Schedule minimizing waiting time
	schedule_basic = loader_schedule.build_loader_schedule(instance, loader_jobs)
	# Schedule by due time
	schedule_sorted = loader_schedule.build_loader_schedule(instance, loader_jobs, loader_schedule.select_job_next)
	# Optimize schedule using Nevergrad
	optimized_jobs = loader_heuristic.optimize_loader_schedule_with_nevergrad(instance, loader_jobs, time_limit)
	schedule_optimized = loader_schedule.build_loader_schedule(instance, optimized_jobs,
	                                                           loader_schedule.select_job_next)

	return [schedule_basic, schedule_sorted, schedule_optimized]


def evaluate_schedules(instance: Instance, loader_schedules: Iterable[Iterable[LoaderRoute]]):
	"""Evaluates schedules and returns the best one."""
	schedule_evaluations = [
	    (objective.calculate_loader_objective_wrong(instance, schedule), schedule) for schedule in loader_schedules
	]

	best_evaluation = min(schedule_evaluations, key=lambda x: x[0])
	return best_evaluation


def save_results(directory: Path, instance: Instance, instance_name: str, vehicle_routes: Iterable[VehicleRoute],
                 best_schedule: Iterable[LoaderRoute], best_objective: int, vehicle_objective: int):
	"""Saves results to solution file and CSV."""
	output_file = directory / f'sol_{instance_name}.json'
	export_solution.export_solution_to_json(vehicle_routes, best_schedule, output_file)

	loader_objective_wrong = objective.calculate_loader_objective_wrong(instance, best_schedule)

	with open(directory / "results.csv", 'a') as f:
		print(
		    instance_name,
		    round_two_digits(best_objective / 10_000),  # Divide by 10_000 to match the original objective scale
		    round_two_digits((vehicle_objective + loader_objective_wrong) / 10_000),
		    sep=',',
		    file=f)


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("instance", type=str, help="Path to the input JSON file.")
	parser.add_argument("-t",
	                    "--time",
	                    type=float,
	                    default=7 * 60.0,
	                    help="Total time limit in seconds (default: 7 minutes).")
	parser.add_argument("-o",
	                    "--output",
	                    type=str,
	                    default=".",
	                    help="Output directory for results (default: current directory).")
	args = parser.parse_args()

	input_path = Path(args.instance)
	instance = Instance.from_json(input_path)
	total_time = args.time
	vehicle_time = total_time * 5 / 7
	loader_time = total_time * 2 / 7
	out_path = Path(args.output)
	instance_name = input_path.stem

	# Build vehicle schedule
	vehicle_routes = pyvrp_model.build_vehicle_schedule(instance, vehicle_time)

	# Collect and sort loader jobs
	loader_jobs = loader_schedule.collect_loader_jobs(instance, (route.clients for route in vehicle_routes))

	# Generate different loader schedules
	loader_schedules = generate_loader_schedules(instance, loader_jobs, loader_time)

	# Evaluate and select the best schedule
	best_objective, best_schedule = evaluate_schedules(instance, loader_schedules)
	vehicle_objective = objective.calculate_vehicle_objective(instance, vehicle_routes)

	# Save results
	save_results(out_path, instance, instance_name, vehicle_routes, best_schedule, best_objective, vehicle_objective)


def round_two_digits(x: float):
	"""Rounds a floating-point number to two decimal places."""
	return math.floor(x * 100 + 0.5) / 100


if __name__ == "__main__":
	main()
