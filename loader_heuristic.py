import time
from typing import Any
from mealpy import PermutationVar, GA, Problem #type: ignore
import nevergrad as ng  # type: ignore
import numpy as np

from instance import Instance
from loader_schedule import LoaderJob, build_loader_schedule, LoaderAssignment, select_job_next
from objective import calculate_loader_objective

class LoaderScheduleProblem(Problem):
    def __init__(self, instance: Instance, jobs_to_permute: list[LoaderJob], minmax: str = "min", **kwargs: Any):
        self.instance = instance
        # The 'items' for PermutationVar are the actual LoaderJob objects.
        # The optimizer will then provide permutations of these objects to obj_func.
        self.jobs=jobs_to_permute
        bounds = PermutationVar(list(range(len(jobs_to_permute))))
        super().__init__(bounds, 'min', log_to='console')

    def obj_func(self, x): # x is a permutation of LoaderJob objects
        # 'x' is one permutation of the original 'jobs_to_permute' list
        ordered_jobs =[self.jobs[i] for i in self.decode_solution(x)['permutation']]

        loader_schedules: list[LoaderAssignment] = build_loader_schedule(self.instance, ordered_jobs, select_job_next)
        objective_value = calculate_loader_objective(self.instance, loader_schedules)

        return objective_value

def optimize_loader_schedule_with_mealpy(
    instance: Instance,
    jobs: list[LoaderJob],
    time:float=60
) -> list[LoaderJob]:
    # 1. Define the problem
    problem = LoaderScheduleProblem(instance,jobs    )

    # 2. Initialize the optimizer
    model = GA.SingleGA()

    # 3. Run the optimization
    model.solve(problem, termination={'max_time': time})

    return [jobs[i] for i in model.problem.decode_solution(model.g_best.solution)['permutation']]

def optimize_loader_schedule_with_nevergrad(
    instance: Instance,
    jobs: list[LoaderJob],
    time_limit: float = 60
) -> list[LoaderJob]:

    def objective_function(x: np.ndarray) -> float:
        # Use argsort to convert the array values into a permutation
        permutation = np.argsort(x)

        # Reorder jobs according to the permutation
        ordered_jobs = [jobs[i] for i in permutation]

        # Build the loader schedule and calculate objective
        loader_schedules: list[LoaderAssignment] = build_loader_schedule(
            instance, ordered_jobs, select_job_next
        )
        objective_value = calculate_loader_objective(instance, loader_schedules)

        return objective_value

    # Create the optimization variable - array of size equal to number of jobs
    # Each element can be any real number, argsort will create the permutation
    num_jobs = len(jobs)
    parametrization = ng.p.Array(shape=(num_jobs,))
    parametrization.random_state.seed(43)

    # Create the optimizer - using OnePlusOne as it's good for continuous optimization
    budget = max(1000000, int(time_limit * 200))
    optimizer = ng.optimizers.NGOpt(parametrization=parametrization, budget=budget)
    start_time=time.time()
    callback=ng.callbacks.EarlyStopping(lambda opt:time.time()-start_time>time_limit)
    optimizer.register_callback('ask',callback)

    res= optimizer.minimize(objective_function,verbosity=0)

    # Convert the best parameters to permutation and return ordered jobs
    best_permutation = np.argsort(res.value)
    return [jobs[i] for i in best_permutation]
