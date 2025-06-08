import pyvrp_model
from instance import Instance


def main():
	instance=Instance.from_json("t1.json")
	res=pyvrp_model.solve_first_stage_model(instance)
	for r in res:
		print(r)

if __name__ == "__main__":
	main()
