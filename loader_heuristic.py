import time

import nevergrad as ng  # type: ignore
import numpy as np

from instance import Instance
from loader_schedule import LoaderJob, build_loader_schedule, LoaderRoute, select_job_next
from objective import calculate_loader_objective


def optimize_loader_schedule_with_nevergrad(instance: Instance, jobs: list[LoaderJob],
                                            time_limit: float) -> list[LoaderJob]:
	"""
	Optimizes the scheduling of loader jobs using the Nevergrad optimization library.

	This function attempts to find an optimal ordering of the given loader jobs to minimize
	the objective value as defined by the loader scheduling problem. It uses a permutation-based
	approach, where the order of jobs is determined by sorting the values of a real-valued vector,
	and Nevergrad is used to optimize this vector within a given time limit.

	Args:
		instance (Instance): The problem instance containing relevant data for scheduling.
		jobs (list[LoaderJob]): A list of loader jobs to be scheduled.
		time_limit (float): The maximum time (in seconds) allowed for the optimization process.

	Returns:
		list[LoaderJob]: The list of jobs reordered according to the optimized schedule.
	"""

	def objective_function(x: np.ndarray[tuple[int], np.dtype[np.float64]]) -> float:
		# Use argsort to convert the array values into a permutation
		permutation = np.argsort(x)

		# Reorder jobs according to the permutation
		ordered_jobs = [jobs[i] for i in permutation]  # type: ignore

		# Build the loader schedule and calculate objective
		loader_schedules: list[LoaderRoute] = build_loader_schedule(
		    instance,
		    ordered_jobs,  # type: ignore
		    select_job_next)
		objective_value = calculate_loader_objective(instance, loader_schedules)

		return objective_value

	# Create the optimization variable - array of size equal to number of jobs
	# Each element can be any real number, argsort will create the permutation
	num_jobs = len(jobs)
	parametrization = ng.p.Array(shape=(num_jobs,))
	parametrization.random_state.seed(43)

	# Create the optimizer
	budget = max(1000000, int(time_limit * 200))
	optimizer = ng.optimizers.NGOpt(parametrization=parametrization, budget=budget)
	start_time = time.time()
	callback = ng.callbacks.EarlyStopping(lambda opt: time.time() - start_time > time_limit)
	optimizer.register_callback('ask', callback)

	# Optimize
	print("Running Nevergrad for building loader schedule")
	res = optimizer.minimize(objective_function, verbosity=0)

	# Convert the best parameters to permutation and return ordered jobs
	best_permutation = np.argsort(res.value)
	return [jobs[i] for i in best_permutation]
