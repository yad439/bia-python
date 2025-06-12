
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
    jobs = jobs.copy()
    jobs.sort(key=lambda j: j.earliest_time)  # Sort by earliest time
    schedules: list[list[LoaderAssignment]] = []  # List of loader schedules
    while jobs:
        # Start a new loader
        loader_schedule: list[LoaderAssignment] = []
        # Find the first unassigned job
        job = jobs[0]
        time = job.earliest_time
        first=job.order_id
        begin_time=job.earliest_time
        while jobs:
            job.loader_cnt -= 1
            if job.loader_cnt == 0:
                jobs.remove(job)  # Remove job if no loaders left
            start_time = max(time, job.order.time_window[0], job.earliest_time)
            finish_time = start_time + job.loader_service_time
            loader_schedule.append(LoaderAssignment(
                order_id=job.order_id,
                arrival_time=time,
                start_time=start_time,
                finish_time=finish_time
            ))
            # Find the next unassigned job the loader can reach in time
            min_wait = math.inf
            next_idx = None
            next_time = None
            for i, j in enumerate(jobs):
                # Loader travels from previous order to this order
                prev_order = job.order
                travel_time = instance.loader_times[prev_order.id][j.order.id]
                arrival = finish_time + travel_time
                start= max(arrival, j.earliest_time)
                finish= start + j.loader_service_time
                back= finish + instance.loader_times[j.order.id][first]
                if arrival > j.earliest_time or back -begin_time > instance.loader_shift_size:
                    continue
                wait = j.earliest_time - arrival
                if wait < min_wait:
                    min_wait = wait
                    next_idx = i
                    next_time = arrival
            if next_idx is None:
                break  # No more jobs for this loader
            assert next_time is not None
            job = jobs[next_idx]
            time = next_time
        if loader_schedule:
            schedules.append(loader_schedule)
    return schedules
