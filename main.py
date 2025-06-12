import export_solution
import loader_schedule
import pyvrp_model
from instance import Instance


def main():
	instance=Instance.from_json("t1.json")
	res=list(pyvrp_model.solve_first_stage_model(instance))
	loader_jobs=loader_schedule.collect_loader_jobs(instance,res)
	loader_schedules=loader_schedule.build_loader_schedule(instance, loader_jobs)
	for r in res:
		print(r)
	for l in loader_schedules:
		print([o.order_id for o in l])
	export_solution.export_solution_to_json(
		instance,
		res,
		loader_schedules,
		"solution.json"
	)

if __name__ == "__main__":
	main()
