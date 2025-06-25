## Usage

### Running Locally with Python

To run the main script on an instance file:

```bash
python3 main.py path/to/instance.json
```

You can specify additional options:

- `-t`, `--time`: Total time limit in seconds (default: 7 minutes)
- `-o`, `--output`: Output directory for results (default: current directory)

Example:

```bash
python3 main.py instances/i1.json -t 420 -o results
```

### Running with Docker

Build the Docker image:

```bash
docker build -t bia-cvrptw .
```

Run the container, mounting your data and output directories:

```bash
docker run --rm -v $(pwd):/app -t bia-cvrptw t1.json -t 420
```
## Output

- Solution JSON files will be saved in the specified output directory.
- A `results.csv` file will be appended with summary results. The header of the file is "instance,corrected_cost,validator_cost"
