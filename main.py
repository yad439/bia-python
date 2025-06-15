from unittest import loader
import export_solution
import loader_heuristic
import loader_schedule
import objective
import pyvrp_model
from instance import Instance


def main():
	instance=Instance.from_json("t1.json")
	res=list(pyvrp_model.solve_first_stage_model(instance))
	loader_jobs=loader_schedule.collect_loader_jobs(instance,(r.clients for r in res))
	loader_jobs.sort(key=lambda x: x.earliest_time)
	loader_schedules1=loader_schedule.build_loader_schedule(instance, loader_jobs)
	loader_schedules2=loader_schedule.build_loader_schedule(instance, loader_jobs, loader_schedule.select_job_next)
	rrr=loader_heuristic.optimize_loader_schedule_with_mealpy(instance,loader_jobs)
	loader_schedules3=loader_schedule.build_loader_schedule(instance, rrr, loader_schedule.select_job_next)
	rrrr=loader_heuristic.optimize_loader_schedule_with_nevergrad(instance,loader_jobs)
	loader_schedules4=loader_schedule.build_loader_schedule(instance, rrrr, loader_schedule.select_job_next)
	# print(rrr)
	for r in res:
		print(r)
	for l in loader_schedules1:
		print([o for o in l.order_ids])
	vc=objective.calculate_vehicle_objective(instance, res)
	loader_objective1=objective.calculate_loader_objective(instance, loader_schedules1)
	loader_objective2=objective.calculate_loader_objective(instance, loader_schedules2)
	loader_objective3=objective.calculate_loader_objective(instance, loader_schedules3)
	loader_objective4=objective.calculate_loader_objective(instance, loader_schedules4)
	print(vc+loader_objective1,vc+loader_objective2,vc+loader_objective3, vc+loader_objective4)
	export_solution.export_solution_to_json(
		instance,
		res,
		loader_schedules1,
		"solution.json"
	)

if __name__ == "__main__":
	main()
