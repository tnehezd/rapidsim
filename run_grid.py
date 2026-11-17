from rapidsim import run_grid

results = run_grid("config_deadzone_grid.yaml")

for result in results:
    print(result.output_dir, result.process.returncode)