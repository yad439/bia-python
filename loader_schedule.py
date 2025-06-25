import copy
from collections.abc import Callable, Iterable
from dataclasses import dataclass
import math

from instance import Instance, Order


@dataclass
class LoaderJob:
	""" A structure representing a loader job for the given vehicle routes."""
	order_id: int
	earliest_time: int
	loader_service_time: int
	loader_cnt: int
	order: Order


def collect_loader_jobs(instance: Instance, vehicle_routes: Iterable[Iterable[tuple[int, int]]]):
	"""
	Collects loader jobs based on the provided instance and vehicle routes.

	This function iterates through the detailed routes and identifies orders that require loader services.
	It creates a list of `LoaderJob` objects for each order that has a non-zero loader count.

	Args:
		instance (Instance): The instance containing order details and other relevant data.
		vehicle_routes (Iterable[Iterable[tuple[int, int]]]): A collection of vehicle routes. The first element of a
			tuple is the order ID and the second element is the arrival time at that order.

	Returns:
		list[LoaderJob]: A list of `LoaderJob` objects representing the loader jobs for the orders
		that require loader services.
	"""
	jobs: list[LoaderJob] = []
	for route in vehicle_routes:
		for order_id, arrival_time in route:
			if order_id == 0:
				continue  # depot
			order = next(o for o in instance.orders if o.id == order_id)
			if order.loader_cnt > 0:
				jobs.append(LoaderJob(order.inner_id, arrival_time, order.loader_service_time, order.loader_cnt, order))
	return jobs


@dataclass
class LoaderRoute:
	"""A structure representing a loader route."""
	order_ids: list[int]
	shift_length: int


def select_job_min_wait(instance: Instance, job_pool: list[LoaderJob], finish_time: int, prev_order: Order,
                        first_order_id: int, begin_time: int):
	"""
	Selects the job from the job pool that minimizes the waiting time for the loader,
	while adhering to constraints such as arrival time and shift size.

	Args:
		instance (Instance): The problem instance containing loader times and shift size.
		job_pool (list[LoaderJob]): A list of loader jobs to choose from.
		finish_time (int): The time at which the previous job finishes.
		prev_order (Order): The previous order completed by the loader.
		first_order_id (int): The ID of the first order in the sequence.
		begin_time (int): The start time of the loader's shift.

	Returns:
		tuple:
			- best_job_idx (int or None): The index of the job in the job pool that minimizes waiting time,
			  or None if no valid job is found.
			- best_arrival_time (int or None): The arrival time for the selected job,
			  or None if no valid job is found.
	"""
	best_job_idx = None
	min_wait = math.inf
	best_arrival_time = None
	for job_idx, candidate_job in enumerate(job_pool):
		# Calculate travel time and arrival
		travel_time = instance.loader_times[prev_order.inner_id][candidate_job.order.inner_id]
		arrival_time = finish_time + travel_time
		candidate_start = max(arrival_time, candidate_job.earliest_time)
		candidate_finish = candidate_start + candidate_job.loader_service_time
		return_time = candidate_finish + instance.loader_times[candidate_job.order.inner_id][first_order_id]

		# Check constraints
		if arrival_time > candidate_job.earliest_time or return_time - begin_time > instance.loader_shift_size:
			continue

		wait_time = candidate_job.earliest_time - arrival_time
		if wait_time < min_wait:
			min_wait = wait_time
			best_job_idx = job_idx
			best_arrival_time = arrival_time
	return best_job_idx, best_arrival_time


def select_job_next(instance: Instance, job_pool: list[LoaderJob], finish_time: int, prev_order: Order,
                    first_order_id: int, begin_time: int):
	"""
	Selects the next job for a loader based from the ordered job pool.

	Args:
		instance (Instance): The problem instance containing loader times and shift size.
		job_pool (list[LoaderJob]): A list of loader jobs available for selection.
		finish_time (int): The finish time of the previous job.
		prev_order (Order): The previous order completed by the loader.
		first_order_id (int): The ID of the first order in the sequence.
		begin_time (int): The start time of the loader's shift.

	Returns:
		tuple:
			- job_idx (int or None): The index of the selected job in the job pool, or None if no job is selected.
			- arrival_time (int or None): The arrival time at the selected job, or None if no job is selected.
	"""
	for job_idx, candidate_job in enumerate(job_pool):
		# Calculate travel time and arrival
		travel_time = instance.loader_times[prev_order.inner_id][candidate_job.order.inner_id]
		arrival_time = finish_time + travel_time
		candidate_start = max(arrival_time, candidate_job.earliest_time)
		candidate_finish = candidate_start + candidate_job.loader_service_time
		return_time = candidate_finish + instance.loader_times[candidate_job.order.inner_id][first_order_id]

		# Check constraints
		if arrival_time > candidate_job.earliest_time or return_time - begin_time > instance.loader_shift_size:
			continue

		return job_idx, arrival_time
	return None, None


def build_loader_schedule(instance: Instance,
                          jobs: list[LoaderJob],
                          job_selector: Callable[[Instance, list[LoaderJob], int, Order, int, int],
                                                 tuple[int | None, int | None]] = select_job_min_wait):
	"""
	Greedily constructs a schedule for loaders based on the given order of jobs and next job selection function.

	Args:
		instance (Instance): The problem instance containing configuration and constraints.
		jobs (list[LoaderJob]): A list of loader jobs to be scheduled.
		job_selector (Callable[[Instance, list[LoaderJob], int, Order, int, int], tuple[int | None, int | None]]):
			A function to select the next job for the loader. Defaults to `select_job_min_wait`.

	Returns:
		list[LoaderRoute]: A list of LoaderRoute objects representing the routes and schedules for the loaders.
	"""
	job_pool = [copy.copy(job) for job in jobs]
	routes: list[LoaderRoute] = []

	while job_pool:
		loader_schedule: list[int] = []
		finish_time = 0

		# Pick the next available job
		current_job = job_pool[0]

		current_time = current_job.earliest_time
		first_order_id = current_job.order_id
		begin_time = current_job.earliest_time

		while job_pool:
			# Assign current job to loader
			current_job.loader_cnt -= 1
			if current_job.loader_cnt == 0:
				job_pool.remove(current_job)

			start_time = max(current_time, current_job.earliest_time)
			finish_time = start_time + current_job.loader_service_time

			loader_schedule.append(current_job.order_id)

			# Find the next best job for this loader
			best_job_idx, best_arrival_time = job_selector(instance, job_pool, finish_time, current_job.order,
			                                               first_order_id, begin_time)

			if best_job_idx is None:
				break  # No more feasible jobs for this loader

			# Move to the next job
			assert best_arrival_time is not None  # This should never be None if best_job_idx is not None
			current_job = job_pool[best_job_idx]
			current_time = best_arrival_time

		if loader_schedule:
			finish_time = finish_time + instance.loader_times[current_job.order.id][first_order_id]
			routes.append(LoaderRoute(loader_schedule, finish_time - begin_time))

	return routes
