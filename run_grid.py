from rapidsim import run

results = run("config_deadzone_grid.yaml")

for result in results:
    print(result.output_dir, result.process.returncode)