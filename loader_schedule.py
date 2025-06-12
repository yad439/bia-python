
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

def collect_loader_jobs(instance: Instance,
                            detailed_routes: list[list[tuple[int, int]]]
                           ):
        jobs: list[LoaderJob] = []
        for route in detailed_routes:
            for order_id, arrival_time in route:
                if order_id == 0:
                    continue  # depot
                order = next(o for o in instance.orders if o.id == order_id)
                if order.loader_cnt > 0:
                    jobs.append(LoaderJob(
                        order_id=order_id,
                        earliest_time=arrival_time,
                        loader_service_time=order.loader_service_time,
                        loader_cnt=order.loader_cnt,
                        order=order
                    ))
        return jobs


@dataclass
class LoaderAssignment:
    order_id: int
    arrival_time: int
    start_time: int
    finish_time: int

def build_loader_schedule(instance: Instance, jobs: list[LoaderJob]):
    # Create a working copy and sort by earliest time
    job_pool = jobs.copy()
    job_pool.sort(key=lambda j: j.earliest_time)

    # Track remaining loader counts for each job using a dictionary for O(1) lookup
    job_counts = {job.order_id: job.loader_cnt for job in job_pool}

    schedules: list[list[LoaderAssignment]] = []

    # Use indices to track available jobs instead of modifying the list
    available_jobs = set(range(len(job_pool)))

    while available_jobs:
        # Start a new loader
        loader_schedule: list[LoaderAssignment] = []

        # Find the earliest available job
        first_job_idx = min(available_jobs, key=lambda i: job_pool[i].earliest_time)
        current_job = job_pool[first_job_idx]

        current_time = current_job.earliest_time
        first_order_id = current_job.order_id
        begin_time = current_job.earliest_time

        while available_jobs:
            # Assign current job to loader
            job_counts[current_job.order_id] -= 1
            if job_counts[current_job.order_id] == 0:
                available_jobs.discard(first_job_idx)

            start_time = max(current_time, current_job.order.time_window[0], current_job.earliest_time)
            finish_time = start_time + current_job.loader_service_time

            loader_schedule.append(LoaderAssignment(
                order_id=current_job.order_id,
                arrival_time=current_time,
                start_time=start_time,
                finish_time=finish_time
            ))

            # Find the next best job for this loader
            best_job_idx = None
            min_wait = math.inf
            best_arrival_time = None

            prev_order = current_job.order

            for job_idx in available_jobs:
                candidate_job = job_pool[job_idx]

                # Calculate travel time and arrival
                travel_time = instance.loader_times[prev_order.id][candidate_job.order.id]
                arrival_time = finish_time + travel_time
                candidate_start = max(arrival_time, candidate_job.earliest_time)
                candidate_finish = candidate_start + candidate_job.loader_service_time
                return_time = candidate_finish + instance.loader_times[candidate_job.order.id][first_order_id]

                # Check constraints
                if arrival_time > candidate_job.earliest_time or return_time - begin_time > instance.loader_shift_size:
                    continue

                wait_time = candidate_job.earliest_time - arrival_time
                if wait_time < min_wait:
                    min_wait = wait_time
                    best_job_idx = job_idx
                    best_arrival_time = arrival_time

            if best_job_idx is None:
                break  # No more feasible jobs for this loader

            # Move to the next job
            assert best_arrival_time is not None  # This should never be None if best_job_idx is not None
            first_job_idx = best_job_idx
            current_job = job_pool[best_job_idx]
            current_time = best_arrival_time

        if loader_schedule:
            schedules.append(loader_schedule)

    return schedules
