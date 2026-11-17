import glob
import os
from dataclasses import dataclass
from typing import Dict, Optional, Sequence, Tuple, Union

import h5py
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.animation import FuncAnimation
from matplotlib.figure import Figure
import numpy as np


MSUN_PER_AU2_TO_CGS = 1.98847e33 / (1.495978707e13 ** 2)
COMPONENT_GROUPS = {
    "gas": "gas_grid",
    "dust": "dust_grid",
    "micron": "micron_grid",
}


@dataclass
class Snapshot:
    time: float
    radius_au: np.ndarray
    surface_density: Dict[str, np.ndarray]


def load_snapshot(path: Union[str, os.PathLike]) -> Snapshot:
    """Load radial grids and surface densities from one RAPID HDF5 snapshot.

    Surface densities are returned in RAPID's native M_sun/AU^2 units.
    """
    with h5py.File(path, "r") as snapshot_file:
        radius = np.asarray(snapshot_file["/gas_grid/radial_grid"][:])
        time = float(snapshot_file["/frame/time"][0])
        densities = {}
        for component, group in COMPONENT_GROUPS.items():
            dataset = "/{}/surface_density".format(group)
            if dataset in snapshot_file:
                density = np.asarray(snapshot_file[dataset][:])
                if density.shape != radius.shape:
                    raise ValueError(
                        "{} in {!r} does not match the gas radial grid.".format(
                            dataset, os.fspath(path)
                        )
                    )
                densities[component] = density
    return Snapshot(time=time, radius_au=radius, surface_density=densities)


def plot_snapshot(
    path: Union[str, os.PathLike],
    components: Sequence[str] = ("gas", "dust", "micron"),
    ax=None,
) -> Tuple[Figure, Axes]:
    """Plot selected surface-density profiles from one RAPID HDF5 snapshot."""
    snapshot = load_snapshot(path)
    unknown = set(components) - set(COMPONENT_GROUPS)
    if unknown:
        raise ValueError("Unknown components: {}".format(", ".join(sorted(unknown))))

    if ax is None:
        figure, ax = plt.subplots()
    else:
        figure = ax.figure

    plotted = 0
    for component in components:
        if component not in snapshot.surface_density:
            continue
        ax.loglog(
            snapshot.radius_au,
            snapshot.surface_density[component] * MSUN_PER_AU2_TO_CGS,
            label=component,
        )
        plotted += 1
    if not plotted:
        raise ValueError(
            "The snapshot contains none of the requested components: {}".format(
                ", ".join(components)
            )
        )

    ax.set_xlabel("Radius [AU]")
    ax.set_ylabel(r"Surface density [g cm$^{-2}$]")
    ax.set_title("RAPID snapshot at t = {:g} yr".format(snapshot.time))
    ax.grid(True, which="both", linestyle="--", alpha=0.4)
    ax.legend()
    figure.tight_layout()
    return figure, ax


def _snapshot_paths(source: Union[str, os.PathLike]) -> list:
    source_path = os.path.abspath(os.fspath(source))
    if os.path.isdir(source_path):
        logs_path = os.path.join(source_path, "LOGS")
        if os.path.isdir(logs_path):
            source_path = logs_path
        paths = sorted(glob.glob(os.path.join(source_path, "snapshot_*.h5")))
    elif os.path.isfile(source_path):
        paths = [source_path]
    else:
        paths = sorted(glob.glob(source_path))
    if not paths:
        raise FileNotFoundError(
            "No RAPID HDF5 snapshots found in {!r}.".format(os.fspath(source))
        )
    return paths


def animate_snapshots(
    source: Union[str, os.PathLike],
    components: Sequence[str] = ("gas", "dust", "micron"),
    interval: int = 200,
    save_path: Optional[Union[str, os.PathLike]] = None,
) -> FuncAnimation:
    """Create an animation of surface-density profiles across HDF5 snapshots.

    ``source`` may be a run directory, its ``LOGS`` directory, one snapshot,
    or a glob pattern. If supplied, ``save_path`` is passed to Matplotlib's
    animation writer (for example, an installed ffmpeg writer for MP4 output).
    """
    if interval < 1:
        raise ValueError("interval must be a positive number of milliseconds.")
    unknown = set(components) - set(COMPONENT_GROUPS)
    if unknown:
        raise ValueError("Unknown components: {}".format(", ".join(sorted(unknown))))

    paths = _snapshot_paths(source)
    first_snapshot = load_snapshot(paths[0])
    figure, ax = plt.subplots()
    lines = {}
    for component in components:
        if component in first_snapshot.surface_density:
            lines[component], = ax.loglog([], [], label=component)
    if not lines:
        raise ValueError("The first snapshot has none of the requested components.")

    ax.set_xlabel("Radius [AU]")
    ax.set_ylabel(r"Surface density [g cm$^{-2}$]")
    ax.grid(True, which="both", linestyle="--", alpha=0.4)
    ax.legend()

    def update(frame_index):
        snapshot = load_snapshot(paths[frame_index])
        for component, line in lines.items():
            density = snapshot.surface_density.get(component)
            if density is None:
                line.set_data([], [])
            else:
                line.set_data(
                    snapshot.radius_au,
                    density * MSUN_PER_AU2_TO_CGS,
                )
        ax.set_title("RAPID snapshot at t = {:g} yr".format(snapshot.time))
        ax.relim()
        ax.autoscale_view()
        return tuple(lines.values())

    animation = FuncAnimation(
        figure,
        update,
        frames=len(paths),
        interval=interval,
        blit=False,
    )
    if save_path is not None:
        animation.save(os.fspath(save_path))
    return animation
