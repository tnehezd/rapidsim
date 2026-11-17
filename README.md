# ``rapidsim`` - a Python interface for the ``RAPID`` simulation code

``rapidsim`` is a lightweight Python interface and command‑line wrapper for the ``RAPID`` (Representative Approach for Particle‑Integrated Disks) simulation code.
It provides a simple, user‑friendly way to run RAPID using a YAML configuration file, without manually invoking the underlying binary or handling command‑line flags directly.

Install the package from PyPI:

```bash
pip install rapidsim
```

After installation, simulations can be launched from the terminal with:

```bash
rapidsim --config config.yaml
```

The source code of ``rapidsim`` is available on GitHub:
https://github.com/tnehezd/rapidsim

The source of ``RAPIP`` is available on GitHub:
https://github.com/tnehezd/RAPID

API reference documentation is available at:
https://rapiddocs.readthedocs.io/en/latest/

### Python API

Run RAPID from Python with either a YAML configuration file or a Python mapping:

```python
from rapidsim import run

run("config.yaml")
```

Run a Cartesian parameter grid concurrently. Grid parameter names use
`section.parameter` keys from the RAPID YAML configuration. Each run writes to
its own subdirectory under `output_dir`; `max_workers` limits concurrent runs.
By default, list-valued parameters vary independently and every combination
is run. Set `mode="paired"` to combine equal-length lists by index instead;
single-value lists are broadcast.

```python
from rapidsim import run_grid

results = run_grid(
    "config.yaml",
    {
        "disk_parameters.alpha_viscosity": [0.001, 0.01],
        "disk_parameters.sigma_profile_exponent": [-0.5, -1.0],
    },
    output_dir="grid_runs",
    max_workers=2,
    mode="cartesian",
)
```

For a YAML-defined grid, put lists directly on the parameters to vary in their
usual configuration sections. Scalar values remain fixed. For dead-zone
transition widths, `deadzone_transition_width_mult` is a shortcut that sets
both inner and outer widths from one scalar or list. Use the individual
`deadzone_inner_transition_width_mult` and
`deadzone_outer_transition_width_mult` keys to vary them independently.
`grid_options` sets the output directory and maximum concurrent runs:

```yaml
deadzone_parameters:
  deadzone_inner_transition_width_mult: [1.0, 1.5, 2.0, 2.5]
  deadzone_outer_transition_width_mult: [1.0, 1.5, 2.0, 2.5]
  # Alternatively, one shared list varies both widths together:
  # deadzone_transition_width_mult: [1.0, 1.5, 2.0, 2.5]

grid_options:
  output_directory: "output_gas_dze"
  max_workers: 2
  mode: cartesian
```

Run the complete example configuration with:

```python
from rapidsim import run_grid

results = run_grid("config_deadzone_grid.yaml")
```

Grid runs display RAPID's startup banner, followed by a fixed-width summary
panel with the full configuration and varied parameter values, then separate
`RUNNING` status for each run. Each RAPID process's output is kept in
`output_directory/logs/run_NNNN.log`. If the requested output directory
already exists, the wrapper selects the next available numbered directory
(for example, `output_gas_dze_0001`) rather than overwriting prior results.
This behavior is implemented in the Python wrapper; the external RAPID
executable is not modified.

HDF5 snapshots can be loaded and plotted with the post-processing module.
Set `output_parameters.output_format` to `hdf5` in the configuration.
`load_snapshot` returns the snapshot time, radial grid, and available component
surface densities in RAPID's native units (M_sun/AU^2).

```python
import matplotlib.pyplot as plt
from rapidsim.postprocessing import load_snapshot, plot_snapshot

snapshot = load_snapshot("grid_runs/run_0001/LOGS/snapshot_00000000.h5")
figure, axes = plot_snapshot("grid_runs/run_0001/LOGS/snapshot_00000000.h5")
plt.show()
```

Animate all snapshots in a run directory or its `LOGS` subdirectory:

```python
import matplotlib.pyplot as plt
from rapidsim.postprocessing import animate_snapshots

animation = animate_snapshots("grid_runs/run_0001")
plt.show()
```


----
### References

If you use this code in your research, please cite the following papers, which provides the theoretical background for the core numerical methods:

```bibtex
@ARTICLE{2017ApJ...851...89R,
      author = {{Reg{\'a}ly}, Zs. and {Juh{\'a}sz}, A. and {Neh{\'e}z}, D.},
      title = "{Interpreting Brightness Asymmetries in Transition Disks: Vortex at Dead Zone or Planet-carved Gap Edges?}",
    journal = {\apj},
   keywords = {accretion, accretion disks, hydrodynamics, methods: numerical, protoplanetary disks, Astrophysics - Earth and Planetary Astrophysics, Astrophysics - Solar and Stellar Astrophysics},
      year = 2017,
      month = dec,
     volume = {851},
     number = {2},
       eid = {89},
      pages = {89},
        doi = {10.3847/1538-4357/aa9a3f},
archivePrefix = {arXiv},
     eprint = {1711.03548},
primaryClass = {astro-ph.EP},
     adsurl = {[https://ui.adsabs.harvard.edu/abs/2017ApJ...851...89R](https://ui.adsabs.harvard.edu/abs/2017ApJ...851...89R)},
    adsnote = {Provided by the SAO/NASA Astrophysics Data System}
}


@article{TarczayNehez2026,
    author = {Tarczay-Neh{\'e}z, D{\'o}ra},
    date = {2026/02/03},
    date-added = {2026-02-03 12:16:24 +0100},
    date-modified = {2026-02-03 12:16:24 +0100},
    doi = {10.1007/s10569-026-10278-2},
    id = {Tarczay-Neh{\'e}z2026},
    isbn = {1572-9478},
    journal = {Celestial Mechanics and Dynamical Astronomy},
    number = {1},
    pages = {6},
    title = {Trajectory-based dust evolution in disks: first results from the RAPID simulation code},
    url = {https://doi.org/10.1007/s10569-026-10278-2},
    volume = {138},
    year = {2026},
    bdsk-url-1 = {https://doi.org/10.1007/s10569-026-10278-2}}
}
