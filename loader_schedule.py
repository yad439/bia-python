from collections.abc import Iterable, Callable
import copy
from dataclasses import dataclass
import math
from instance import Instance, Order

@dataclass
class LoaderJob:
    order_id: int
    earliest_time: int
    loader_service_time: int
    loader_cnt: int
    order: Order

def collect_loader_jobs(instance: Instance,detailed_routes: Iterable[Iterable[tuple[int, int]]]):
        jobs: list[LoaderJob] = []
        for route in detailed_routes:
            for order_id, arrival_time in route:
                if order_id == 0:
                    continue  # depot
                order = next(o for o in instance.orders if o.id == order_id)
                if order.loader_cnt > 0:
                    jobs.append(LoaderJob(
                        order_id=order.inner_id,
                        earliest_time=arrival_time,
                        loader_service_time=order.loader_service_time,
                        loader_cnt=order.loader_cnt,
                        order=order
                    ))
        return jobs


@dataclass
class LoaderAssignment:
    order_ids: list[int]
    shift_length:int

def select_job_min_wait(instance: Instance, job_pool: list[LoaderJob], finish_time: int, prev_order: Order, first_order_id: int, begin_time: int):
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

def select_job_next(instance: Instance, job_pool: list[LoaderJob], finish_time: int, prev_order: Order, first_order_id: int, begin_time: int):
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

        return job_idx,arrival_time
    return None, None

def build_loader_schedule(instance: Instance, jobs: list[LoaderJob],
                         job_selector: Callable[[Instance, list[LoaderJob], int, Order, int, int], tuple[int | None, int | None]] = select_job_min_wait):
    # Create a working copy and sort by earliest time
    job_pool = [copy.copy(job) for job in jobs]
    # job_pool.sort(key=lambda j: j.earliest_time)

    schedules: list[LoaderAssignment] = []

    while job_pool:
        # Start a new loader
        loader_schedule: list[int] = []

        # Find the earliest available job
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
            best_job_idx, best_arrival_time = job_selector(
                instance, job_pool, finish_time, current_job.order, first_order_id, begin_time
            )

            if best_job_idx is None:
                break  # No more feasible jobs for this loader

            # Move to the next job
            assert best_arrival_time is not None  # This should never be None if best_job_idx is not None
            current_job = job_pool[best_job_idx]
            current_time = best_arrival_time

        if loader_schedule:
            #finish_time=finish_time #+ instance.loader_times[current_job.order.id][first_order_id]+ instance.orders[first_order_id].loader_service_time
            schedules.append(LoaderAssignment(loader_schedule, finish_time - begin_time))

    return schedules
