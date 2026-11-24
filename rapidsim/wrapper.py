import argparse
import copy
import datetime
import importlib.metadata
import itertools
import math
import os
import re
import subprocess
import sys
import textwrap
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Union

import yaml


PREFIX = "[PY-WRAPPER: RAPIDSIM]"
ConfigSource = Union[str, os.PathLike, Mapping[str, Any]]

YAML_TO_C_MAPPING = {
    "enable_dust_drift": "drift",
    "enable_dust_growth": "growth",
    "enable_gas_evolution": "evol",
    "enable_photoevaporation": "photoevap",
    "enable_two_dust_populations": "twopop",
    "fragmentation_velocity": "ufrag",
    "fragmentation_factor": "ffrag",
    "inner_boundary_condition": "inner_bc",
    "radial_grid_type": "grid_type",
    "outer_boundary_condition": "outer_bc",
    "number_of_grid_points": "ngrid_val",
    "number_of_dust_particles": "ndust_val",
    "inner_radius_au": "rmin_val",
    "outer_radius_au": "rmax_val",
    "initial_gas_sigma0_msun_per_au2": "sigma0_val",
    "disk_mass": "disk_mass",
    "total_disk_mass": "disk_mass",
    "sigma_profile_exponent": "sigmap_exp_val",
    "alpha_viscosity": "alpha_visc_val",
    "star_mass_msun": "star_val",
    "aspect_ratio_at_1au": "hasp_val",
    "flaring_index": "flind_val",
    "photoevaporation_mode": "photoevap_mode",
    "xray_luminosity_erg_s": "xray_lum",
    "use_cutoff_for_gas": "cutoff",
    "characteristic_cutoff_radius_au": "cutoff_radius",
    "cutoff_sharpness_factor": "cutoff_sharpness",
    "density_floor": "density_floor",
    "dust_density_floor": "dust_density_floor",
    "gaussian_smoothing_sigma_grid_units": "gaussian_smoothing_sigma_grid_units",
    "gaussian_smoothing_cutoff_sigma": "gaussian_smoothing_cutoff_sigma",
    "deadzone_inner_radius_au": "r_dze_i_val",
    "deadzone_outer_radius_au": "r_dze_o_val",
    "deadzone_inner_transition_width": "dr_dze_i_val",
    "deadzone_inner_transition_width_mult": "dr_dze_i_val",
    "deadzone_outer_transition_width": "dr_dze_o_val",
    "deadzone_outer_transition_width_mult": "dr_dze_o_val",
    "deadzone_alpha_reduction": "a_mod_val",
    "initial_dust_to_gas_ratio": "eps_val",
    "population_one_mass_ratio": "ratio_val",
    "micro_particle_size_cm": "mic_val",
    "large_size_particle_value_cm": "onesize_val",
    "one_size_particle_value_cm": "onesize_val",
    "constant_stokes_number": "fixed_stokes",
    "dust_particle_density_g_cm3": "pdensity_val",
    "input_file_path": "input_file",
    "output_directory_name": "output_dir_name",
    "output_format": "output_format",
    "fixed_time_step": "tStep",
    "total_simulation_time": "totalTime",
    "output_write_frequency": "outputFrequency",
    "dust_smoothing_mode": "dust_smoothing_mode",
    "test_mode": "test_mode",
}

C_ARG_MAPPING = {
    "drift": "-drift",
    "growth": "-growth",
    "evol": "-evol",
    "twopop": "-twopop",
    "ufrag": "-ufrag",
    "ffrag": "-ffrag",
    "photoevap": "-photoevap",
    "ngrid_val": "-n",
    "ndust_val": "-ndust",
    "rmin_val": "-ri",
    "rmax_val": "-ro",
    "grid_type": "-grid_type",
    "inner_bc": "-inner_bc",
    "outer_bc": "-outer_bc",
    "sigma0_val": "-sigma0_init",
    "sigmap_exp_val": "-index_init",
    "alpha_visc_val": "-alpha_init",
    "star_val": "-stellar_mass",
    "disk_mass": "-disk_mass",
    "hasp_val": "-h_init",
    "flind_val": "-flind_init",
    "photoevap_mode": "-photoevap_mode",
    "xray_lum": "-xray_luminosity",
    "cutoff": "-cutoff",
    "cutoff_radius": "-cutoff_radius",
    "cutoff_sharpness": "-cutoff_sharpness",
    "r_dze_i_val": "-rdzei",
    "r_dze_o_val": "-rdzeo",
    "dr_dze_i_val": "-drdzei",
    "dr_dze_o_val": "-drdzeo",
    "a_mod_val": "-amod",
    "density_floor": "-density_floor",
    "dust_density_floor": "-dust_density_floor",
    "eps_val": "-eps",
    "ratio_val": "-ratio",
    "mic_val": "-micsize",
    "onesize_val": "-largesize",
    "fixed_stokes": "-stokes",
    "pdensity_val": "-pdensity",
    "test_mode": "-test",
    "gaussian_smoothing_sigma_grid_units": "-gaussian_sigma_grid_units",
    "gaussian_smoothing_cutoff_sigma": "-gaussian_cutoff_sigma",
    "input_file": "-i",
    "output_dir_name": "-o",
    "output_format": "--output-format",
    "dust_smoothing_mode": "-dust_smoothing",
    "tStep": "-tStep",
    "totalTime": "-tmax",
    "outputFrequency": "-outfreq",
}

YAML_SECTIONS = (
    "simulation_parameters",
    "disk_parameters",
    "boundary_conditions",
    "deadzone_parameters",
    "dust_parameters",
    "output_parameters",
    "time_parameters",
    "log_parameters",
    "photoevaporation_parameters",
    "cutoff_profile_parameters",
)

PANEL_SECTION_LABELS = {
    "simulation_parameters": "SIMULATION OPTIONS",
    "disk_parameters": "INITIALIZATION PARAMETERS",
    "boundary_conditions": "BOUNDARY CONDITIONS",
    "deadzone_parameters": "DEAD-ZONE PARAMETERS",
    "dust_parameters": "DUST PARAMETERS",
    "output_parameters": "OUTPUT PARAMETERS",
    "time_parameters": "TIME PARAMETERS",
    "log_parameters": "LOG PARAMETERS",
    "photoevaporation_parameters": "PHOTOEVAPORATION PARAMETERS",
    "cutoff_profile_parameters": "INITIAL GAS PROFILE",
}

PANEL_PARAMETER_LABELS = {
    "simulation_parameters.enable_gas_evolution": "Gas evolution",
    "simulation_parameters.enable_dust_drift": "Dust drift",
    "simulation_parameters.enable_dust_growth": "Dust growth",
    "simulation_parameters.enable_photoevaporation": "Photoevaporation",
    "simulation_parameters.fragmentation_velocity": "Fragmentation velocity (cm/s)",
    "simulation_parameters.fragmentation_factor": "Fragmentation factor",
    "dust_parameters.one_size_particle_value_cm": "Fixed grain radius (cm)",
    "dust_parameters.large_size_particle_value_cm": "Fixed grain radius (cm)",
    "dust_parameters.constant_stokes_number": "Constant Stokes number",
    "disk_parameters.star_mass_msun": "Stellar mass (Solar Mass)",
    "disk_parameters.aspect_ratio_at_1au": "Disk aspect ratio (H/R)",
    "disk_parameters.flaring_index": "Disk flaring index",
    "disk_parameters.alpha_viscosity": "Alpha viscosity",
    "disk_parameters.disk_mass": "Total disk mass (Solar Mass)",
    "disk_parameters.inner_radius_au": "Inner disk edge (AU)",
    "disk_parameters.outer_radius_au": "Outer disk edge (AU)",
    "disk_parameters.sigma_profile_exponent": "Surface density profile exponent",
    "disk_parameters.number_of_grid_points": "Number of gas grid points",
    "disk_parameters.number_of_dust_particles": "Number of dust particles",
    "boundary_conditions.inner_boundary_condition": "INNER BC",
    "boundary_conditions.outer_boundary_condition": "OUTER BC",
    "deadzone_parameters.deadzone_inner_radius_au": "Dead-zone inner edge (AU)",
    "deadzone_parameters.deadzone_outer_radius_au": "Dead-zone outer edge (AU)",
    "deadzone_parameters.deadzone_inner_transition_width_mult":
        "Inner transition width multiplier",
    "deadzone_parameters.deadzone_outer_transition_width_mult":
        "Outer transition width multiplier",
    "deadzone_parameters.deadzone_transition_width_mult":
        "Dead-zone transition width multiplier",
    "deadzone_parameters.deadzone_alpha_reduction": "Dead-zone alpha reduction",
}


@dataclass
class GridRunResult:
    parameters: Dict[str, Any]
    output_dir: str
    process: subprocess.CompletedProcess
    log_file: Optional[str] = None


class GridRunError(RuntimeError):
    def __init__(self, results: List[GridRunResult]):
        self.results = results
        failed = [result for result in results if result.process.returncode != 0]
        super().__init__(
            "{} of {} RAPID grid runs failed; inspect the `results` attribute.".format(
                len(failed), len(results)
            )
        )


def get_version():
    try:
        return importlib.metadata.version("rapidsim")
    except importlib.metadata.PackageNotFoundError:
        package_dir = os.path.dirname(os.path.abspath(__file__))
        for path_candidate in (
            os.path.join(package_dir, "..", "pyproject.toml"),
            os.path.join(package_dir, "pyproject.toml"),
            os.path.join(package_dir, "..", "setup.py"),
            os.path.join(package_dir, "setup.py"),
        ):
            if os.path.exists(path_candidate):
                with open(path_candidate, "r", encoding="utf-8") as file:
                    match = re.search(
                        r'version\s*=\s*["\']([^"\']+)["\']', file.read()
                    )
                    if match:
                        return match.group(1)
        return "unknown"


def _get_rapidsim_header() -> str:
    border = "=" * 74
    return "\n".join(
        (
            border,
            "|| {:^68} ||".format("RAPIDSIM PYTHON PACKAGE"),
            "|| {:^68} ||".format("Version: {}".format(get_version())),
            border,
        )
    )


def _read_config(config: ConfigSource) -> Dict[str, Any]:
    if isinstance(config, Mapping):
        parsed = copy.deepcopy(dict(config))
    else:
        config_path = os.path.abspath(os.fspath(config))
        with open(config_path, "r", encoding="utf-8") as file:
            parsed = yaml.safe_load(file) or {}
    if not isinstance(parsed, dict):
        raise ValueError("The simulation configuration must be a YAML mapping.")
    return parsed


def _merge_config(target: Dict[str, Any], updates: Mapping[str, Any]) -> None:
    for key, value in updates.items():
        if isinstance(value, Mapping) and isinstance(target.get(key), dict):
            _merge_config(target[key], value)
        else:
            target[key] = copy.deepcopy(value)


def _section(config: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    values = config.get(name, {})
    if values is None:
        return {}
    if not isinstance(values, Mapping):
        raise ValueError("Configuration section {!r} must be a mapping.".format(name))
    return values


def _find_binary() -> str:
    package_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = (
        os.path.join(package_dir, "data", "simulation"),
        os.path.join(package_dir, "bin", "simulation"),
        os.path.abspath(os.path.join(package_dir, "..", "bin", "simulation")),
        os.path.abspath("./bin/simulation"),
        os.path.abspath("../bin/simulation"),
    )
    for path in possible_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    raise FileNotFoundError(
        "Could not find an executable RAPID `simulation` binary. Tried:\n"
        + "\n".join(possible_paths)
    )


def _get_rapid_header(binary_path: str) -> str:
    # RAPID prints its banner before parsing arguments. The invalid version flag
    # makes the probe exit before simulation setup.
    probe = subprocess.run(
        [binary_path, "--version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
        timeout=10,
    )
    output_lines = (probe.stdout or "").splitlines()
    border_indexes = [
        index
        for index, line in enumerate(output_lines)
        if re.fullmatch(r"=+", line)
    ]
    if len(border_indexes) < 2:
        raise RuntimeError(
            "Could not read the RAPID startup banner from {!r}."
            .format(binary_path)
        )
    header = "\n".join(output_lines[border_indexes[0]:border_indexes[1] + 1])
    if not re.search(r"\bVersion:\s*\S+", header):
        raise RuntimeError(
            "The RAPID startup banner from {!r} did not contain a version."
            .format(binary_path)
        )
    return header


def _build_command(config: Mapping[str, Any], binary_path: str) -> List[str]:
    parameters = {}
    deadzone_parameters = _section(config, "deadzone_parameters")
    shared_width = deadzone_parameters.get("deadzone_transition_width_mult")
    if shared_width is not None:
        if isinstance(shared_width, (list, tuple)):
            raise ValueError(
                "List-valued parameters must be run through run_grid()."
            )
        for width_name in (
            "deadzone_inner_transition_width_mult",
            "deadzone_outer_transition_width_mult",
        ):
            if width_name not in deadzone_parameters:
                c_key = YAML_TO_C_MAPPING[width_name]
                parameters[c_key] = shared_width

    for section in YAML_SECTIONS:
        section_values = _section(config, section)
        for yaml_key, c_key in YAML_TO_C_MAPPING.items():
            if yaml_key in section_values:
                parameters[c_key] = section_values[yaml_key]

    if any(isinstance(value, (list, tuple)) for value in parameters.values()):
        raise ValueError(
            "List-valued parameters must be resolved before running RAPID."
        )

    if "fixed_stokes" in parameters:
        stokes = parameters["fixed_stokes"]
        if (isinstance(stokes, bool) or not isinstance(stokes, (int, float))
                or not math.isfinite(stokes) or stokes <= 0):
            raise ValueError("constant_stokes_number must be a finite positive number.")
        if (parameters.get("drift", True) != True
                or parameters.get("growth", True) != False
                or parameters.get("twopop", True) != False):
            raise ValueError(
                "constant_stokes_number requires dust drift enabled, "
                "dust growth disabled and two dust populations disabled."
            )
        if (parameters.get("onesize_val", 0) != 0
                or parameters.get("input_file") is not None
                or parameters.get("test_mode") is not None):
            raise ValueError(
                "constant_stokes_number cannot be combined with a fixed grain "
                "size, an input profile or a benchmark mode."
            )

    command = [binary_path]
    log_parameters = _section(config, "log_parameters")
    verbosity = log_parameters.get("info_level", "none")
    if verbosity == "info":
        command.append("-v")
    elif verbosity == "debug":
        command.append("-vv")

    for key, value in parameters.items():
        flag = C_ARG_MAPPING[key]
        if isinstance(value, bool):
            command.extend((flag, "1.0" if value else "0.0"))
        elif flag in ("-i", "-o", "-test"):
            if value is not None and str(value).strip():
                command.extend((flag, str(value)))
            elif flag == "-o":
                command.extend((flag, "output"))
        else:
            command.extend((flag, str(value)))
    return command


def _normalize_inline_parameter_lists(config: Dict[str, Any]) -> bool:
    has_grid = False
    for section in YAML_SECTIONS:
        section_values = config.get(section)
        if section_values is None:
            continue
        if not isinstance(section_values, dict):
            raise ValueError(
                "Configuration section {!r} must be a mapping.".format(section)
            )
        for name, value in list(section_values.items()):
            if not isinstance(value, (list, tuple)):
                continue
            if not value:
                raise ValueError(
                    "List-valued parameter '{}.{}' cannot be empty.".format(
                        section, name
                    )
                )
            if len(value) > 1:
                has_grid = True
            else:
                section_values[name] = value[0]
    return has_grid


def run(
    config: ConfigSource = "config.yaml",
    overrides: Optional[Mapping[str, Any]] = None,
    output_dir: Optional[Union[str, os.PathLike]] = None,
    check: bool = True,
    cwd: Optional[Union[str, os.PathLike]] = None,
    env: Optional[Mapping[str, str]] = None,
    log_file: Optional[Union[str, os.PathLike]] = None,
) -> Union[subprocess.CompletedProcess, List[GridRunResult]]:
    """Run RAPID once, or run a grid when a parameter has multiple values."""
    full_config = _read_config(config)
    if overrides:
        _merge_config(full_config, overrides)
    if output_dir is not None:
        output_parameters = full_config.setdefault("output_parameters", {})
        if not isinstance(output_parameters, dict):
            raise ValueError("Configuration section 'output_parameters' must be a mapping.")
        output_parameters["output_directory_name"] = os.fspath(output_dir)

    has_grid = _normalize_inline_parameter_lists(full_config)
    if has_grid or full_config.get("parameter_grid") is not None:
        if log_file is not None:
            raise ValueError(
                "'log_file' is not supported for grid runs; each run gets its own log."
            )
        config_label = (
            "<in-memory configuration>"
            if isinstance(config, Mapping)
            else os.path.abspath(os.fspath(config))
        )
        return run_grid(
            full_config,
            output_dir=output_dir,
            check=check,
            cwd=cwd,
            env=env,
            _config_label=config_label,
        )

    if (
        _section(full_config, "log_parameters").get("disable_terminal_panels", False)
        and log_file is None
    ):
        raise ValueError(
            "'disable_terminal_panels' is supported for grid runs only; "
            "RAPID's standalone executable has no such command-line option."
        )

    binary_path = _find_binary()
    command = _build_command(full_config, binary_path)
    current_env = os.environ.copy()
    current_env.update(env or {})
    configured_threads = _section(full_config, "simulation_parameters").get(
        "omp_num_threads"
    )
    current_env["OMP_NUM_THREADS"] = str(
        configured_threads or current_env.get("OMP_NUM_THREADS", "1")
    )

    if log_file is None:
        print(_get_rapidsim_header())
        print("\n{} --- Running: Main Simulation Program ---".format(PREFIX))
        print(
            "{} The current command-line arguments are:\n simulation {}".format(
                PREFIX, " ".join(command[1:])
            )
        )
        print("{} Setting OMP_NUM_THREADS={} for this run.".format(
            PREFIX, current_env["OMP_NUM_THREADS"]
        ))
        print(
            "{} Start running the binary ({}) at {}...\n".format(
                PREFIX,
                binary_path,
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
        )
        return subprocess.run(
            command,
            check=check,
            env=current_env,
            cwd=os.fspath(cwd) if cwd is not None else None,
        )

    log_path = os.path.abspath(os.fspath(log_file))
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "w", encoding="utf-8", errors="replace") as output:
        return subprocess.run(
            command,
            check=check,
            env=current_env,
            cwd=os.fspath(cwd) if cwd is not None else None,
            stdout=output,
            stderr=subprocess.STDOUT,
        )


def _set_config_value(config: Dict[str, Any], dotted_key: str, value: Any) -> None:
    parts = dotted_key.split(".")
    if len(parts) != 2 or parts[0] not in YAML_SECTIONS:
        raise ValueError(
            "Grid parameters must use `section.parameter` keys, got {!r}.".format(
                dotted_key
            )
        )
    if dotted_key == "deadzone_parameters.deadzone_transition_width_mult":
        section = config.setdefault(parts[0], {})
        if not isinstance(section, dict):
            raise ValueError(
                "Configuration section {!r} must be a mapping.".format(parts[0])
            )
        section.setdefault("deadzone_inner_transition_width_mult", value)
        section.setdefault("deadzone_outer_transition_width_mult", value)
        return
    if parts[1] not in YAML_TO_C_MAPPING and parts[1] != "omp_num_threads":
        raise ValueError("Unsupported RAPID configuration parameter: {!r}.".format(
            dotted_key
        ))
    if dotted_key == "output_parameters.output_directory_name":
        raise ValueError("Grid runs assign separate output directories automatically.")
    section = config.setdefault(parts[0], {})
    if not isinstance(section, dict):
        raise ValueError("Configuration section {!r} must be a mapping.".format(parts[0]))
    section[parts[1]] = value


def _flatten_parameter_grid(
    parameter_grid: Mapping[str, Any],
) -> Dict[str, Sequence[Any]]:
    flattened = {}
    for section, parameters in parameter_grid.items():
        if "." in section:
            flattened[section] = parameters
            continue
        if section not in YAML_SECTIONS or not isinstance(parameters, Mapping):
            raise ValueError(
                "Grid parameters must be grouped by RAPID YAML section, got {!r}."
                .format(section)
            )
        for name, choices in parameters.items():
            flattened["{}.{}".format(section, name)] = choices
    return flattened


def _extract_inline_parameter_grid(
    config: Dict[str, Any],
) -> Dict[str, Sequence[Any]]:
    parameter_grid = {}
    for section in YAML_SECTIONS:
        section_values = config.get(section)
        if section_values is None:
            continue
        if not isinstance(section_values, dict):
            raise ValueError(
                "Configuration section {!r} must be a mapping.".format(section)
            )
        for name, value in list(section_values.items()):
            if isinstance(value, (list, tuple)):
                parameter_grid["{}.{}".format(section, name)] = value
                del section_values[name]
    return parameter_grid


def _print_grid_panel(lines: Sequence[str]) -> None:
    width = 74
    content_width = width - 6
    border = "=" * width
    print()
    print(border)
    print("|| {:<{}} ||".format("RAPIDSIM PARAMETER GRID", content_width))
    print(border)
    for line in lines:
        indent = len(line) - len(line.lstrip())
        text = line.strip()
        if os.path.isabs(text):
            path_parts = text.split(os.sep)[1:]
            current = os.sep
            wrapped_lines = []
            for part in path_parts:
                separator = "" if current.endswith(os.sep) else os.sep
                candidate = current + separator + part
                if len(candidate) + indent > content_width and current != os.sep:
                    wrapped_lines.append(current + os.sep)
                    current = "  " + part
                else:
                    current = candidate
            wrapped_lines.append(current)
        else:
            wrapped_lines = textwrap.wrap(
                text,
                width=content_width - indent,
                subsequent_indent="  ",
                break_long_words=True,
                break_on_hyphens=False,
            ) or [""]
        for wrapped_line in wrapped_lines:
            panel_line = " " * indent + wrapped_line
            print("|| {:<{}} ||".format(panel_line, content_width))
    print(border, flush=True)


def _format_panel_parameter(dotted_name: str, value: Any) -> str:
    parameter = dotted_name.rsplit(".", 1)[-1]
    label = PANEL_PARAMETER_LABELS.get(
        dotted_name,
        parameter.replace("_", " ").title(),
    )
    if isinstance(value, (list, tuple)):
        display_value = ", ".join(str(item) for item in value)
    else:
        display_value = str(value)
    return "    {:<40} [{}]".format("{}:".format(label), display_value)


def run_grid(
    config: ConfigSource,
    parameter_grid: Optional[Mapping[str, Any]] = None,
    output_dir: Optional[Union[str, os.PathLike]] = None,
    max_workers: Optional[int] = None,
    mode: Optional[str] = None,
    check: bool = True,
    cwd: Optional[Union[str, os.PathLike]] = None,
    env: Optional[Mapping[str, str]] = None,
    _config_label: Optional[str] = None,
) -> List[GridRunResult]:
    """Run a parameter grid from YAML or an explicit mapping, concurrently.

    In YAML, list-valued parameters inside regular configuration sections are
    varied automatically. By default, every possible combination is run;
    ``mode="paired"`` combines equal-length lists by index.
    """
    base_config = _read_config(config)
    yaml_grid = base_config.pop("parameter_grid", None)
    inline_grid = _extract_inline_parameter_grid(base_config)
    grid_options = base_config.pop("grid_options", {})
    if not isinstance(grid_options, Mapping):
        raise ValueError("Configuration section 'grid_options' must be a mapping.")
    unknown_options = set(grid_options) - {"output_directory", "max_workers"}
    if unknown_options:
        raise ValueError(
            "Unknown grid option(s): {}.".format(", ".join(sorted(unknown_options)))
        )
    if parameter_grid is None:
        if yaml_grid is not None and inline_grid:
            raise ValueError(
                "Specify grid values either inline in RAPID parameters or in "
                "the legacy 'parameter_grid' section, not both."
            )
        parameter_grid = inline_grid or yaml_grid
    elif yaml_grid is not None or inline_grid:
        raise ValueError(
            "Pass parameter_grid explicitly or define list-valued parameters "
            "in the config, not both."
        )
    if output_dir is None:
        output_dir = grid_options.get("output_directory", "rapidsim_grid")
    if max_workers is None:
        max_workers = grid_options.get("max_workers")
    if mode is not None:
        if not isinstance(mode, str) or mode.lower() != "paired":
            raise ValueError("Grid mode must be 'paired' or omitted.")
        mode = mode.lower()

    if not isinstance(parameter_grid, Mapping) or not parameter_grid:
        raise ValueError(
            "Define at least one list-valued RAPID parameter in the config "
            "or pass a parameter_grid mapping."
        )
    parameter_grid = _flatten_parameter_grid(parameter_grid)
    if not parameter_grid:
        raise ValueError("parameter_grid must contain at least one parameter.")
    if max_workers is not None and (
        isinstance(max_workers, bool)
        or not isinstance(max_workers, int)
        or max_workers < 1
    ):
        raise ValueError("max_workers must be a positive integer or None.")

    parameter_names = list(parameter_grid)
    values = []
    for name in parameter_names:
        choices = parameter_grid[name]
        if isinstance(choices, (str, bytes)) or not isinstance(choices, Sequence):
            raise TypeError("Values for {!r} must be a sequence.".format(name))
        if not choices:
            raise ValueError("Values for {!r} cannot be empty.".format(name))
        values.append(list(choices))

    if mode == "paired":
        run_count = max(len(choices) for choices in values)
        invalid_lengths = [
            len(choices)
            for choices in values
            if len(choices) not in (1, run_count)
        ]
        if invalid_lengths:
            lengths = ", ".join(
                "{}={}".format(name, len(choices))
                for name, choices in zip(parameter_names, values)
            )
            raise ValueError(
                "Paired grid values must have matching lengths (or length 1); "
                "got {}. Omit mode to run all combinations.".format(lengths)
            )
        paired_values = [
            choices * run_count if len(choices) == 1 else choices
            for choices in values
        ]
        combinations = [
            dict(zip(parameter_names, values_for_run))
            for values_for_run in zip(*paired_values)
        ]
    else:
        combinations = [
            dict(zip(parameter_names, values_for_run))
            for values_for_run in itertools.product(*values)
        ]
    for name in parameter_names:
        _set_config_value(copy.deepcopy(base_config), name, values[
            parameter_names.index(name)
        ][0])

    requested_root = os.path.abspath(os.fspath(output_dir))
    parent, root_name = os.path.split(requested_root)
    if not root_name:
        raise ValueError("Grid output directory cannot be a filesystem root.")
    os.makedirs(parent, exist_ok=True)
    suffix = 0
    while True:
        root = (
            requested_root
            if suffix == 0
            else "{}_{:04d}".format(requested_root, suffix)
        )
        try:
            os.mkdir(root)
            break
        except FileExistsError:
            suffix += 1

    run_dirs = [
        os.path.join(root, "run_{:04d}".format(index))
        for index in range(1, len(combinations) + 1)
    ]
    log_dir = os.path.join(root, "logs")
    log_paths = [
        os.path.join(log_dir, "run_{:04d}.log".format(index))
        for index in range(1, len(combinations) + 1)
    ]
    os.makedirs(log_dir, exist_ok=True)

    def execute(index: int, parameters: Dict[str, Any]) -> GridRunResult:
        status_lines = [
            "[RUNNING {:02d}/{:02d}] run_{:04d}".format(
                index + 1,
                len(combinations),
                index + 1,
            )
        ]
        status_lines.extend(
            "  {} = {!r}".format(name, value)
            for name, value in parameters.items()
        )
        status_lines.extend(
            (
                "  Output: {}".format(run_dirs[index]),
                "  Log: {}".format(log_paths[index]),
            )
        )
        print("\n".join(status_lines), flush=True)
        run_config = copy.deepcopy(base_config)
        for name, value in parameters.items():
            _set_config_value(run_config, name, value)
        run_options = {
            "output_dir": run_dirs[index],
            "check": False,
            "log_file": log_paths[index],
        }
        if cwd is not None:
            run_options["cwd"] = cwd
        if env is not None:
            run_options["env"] = env
        process = run(run_config, **run_options)
        return GridRunResult(
            parameters,
            run_dirs[index],
            process,
            log_paths[index],
        )

    worker_count = max_workers or min(len(combinations), os.cpu_count() or 1)
    rapid_header = _get_rapid_header(_find_binary())
    print(_get_rapidsim_header(), flush=True)
    print(rapid_header, flush=True)
    config_label = _config_label or (
        "<in-memory configuration>"
        if isinstance(config, Mapping)
        else os.path.abspath(os.fspath(config))
    )
    panel_lines = [
        "GRID SUMMARY",
        "  {:<26} [{}]".format("Runs:", len(combinations)),
        "  {:<26} [{}]".format("Parallel workers:", worker_count),
        "  Output directory:",
        "    {}".format(root),
        "  Base config:",
        "    {}".format(config_label),
        "  RAPID logs:",
        "    {}".format(log_dir),
    ]
    panel_lines.append("PARAMETERS")
    varied_parameters_by_section = {}
    for name, choices in zip(parameter_names, values):
        section, parameter = name.split(".", 1)
        varied_parameters_by_section.setdefault(section, {})[parameter] = choices

    for section in YAML_SECTIONS:
        section_values = base_config.get(section)
        if not isinstance(section_values, Mapping):
            section_values = {}
        varied_values = varied_parameters_by_section.get(section, {})
        if not section_values and not varied_values:
            continue
        panel_lines.append(
            "  {}".format(PANEL_SECTION_LABELS.get(section, section.upper()))
        )
        for name, value in section_values.items():
            dotted_name = "{}.{}".format(section, name)
            if dotted_name in parameter_grid:
                continue
            panel_lines.append(_format_panel_parameter(dotted_name, value))
        for name, choices in varied_values.items():
            panel_lines.append(
                _format_panel_parameter(
                    "{}.{}".format(section, name),
                    choices,
                )
            )
    _print_grid_panel(panel_lines)

    results_by_index = {}
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = {
            executor.submit(execute, index, parameters): index
            for index, parameters in enumerate(combinations)
        }
        for future in as_completed(futures):
            index = futures[future]
            result = future.result()
            results_by_index[index] = result
            print(
                "{} Grid run {}/{} finished with exit code {}.".format(
                    PREFIX, index + 1, len(combinations), result.process.returncode
                )
            )

    results = [results_by_index[index] for index in range(len(combinations))]
    if check and any(result.process.returncode != 0 for result in results):
        raise GridRunError(results)
    return results


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Runs the simulation workflow with YAML configuration."
    )
    parser.add_argument(
        "-c", "--config", default="config.yaml", help="Path to the YAML configuration file."
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s {}".format(get_version())
    )
    args = parser.parse_args(argv)

    try:
        result = run(args.config, check=False)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print("{} Error: {}".format(PREFIX, exc), file=sys.stderr)
        return 1

    if isinstance(result, list):
        failed_results = [
            grid_result
            for grid_result in result
            if grid_result.process.returncode != 0
        ]
        if not failed_results:
            print(
                "\n{} Grid simulation completed successfully ({} runs).".format(
                    PREFIX, len(result)
                )
            )
            return 0
        return_code = failed_results[0].process.returncode
        print(
            "\n{} Grid simulation had {} failed run(s); first error code: {}".format(
                PREFIX, len(failed_results), return_code
            ),
            file=sys.stderr,
        )
        return return_code

    if result.returncode == 0:
        print("\n{} Main Simulation Program completed successfully.".format(PREFIX))
    else:
        print(
            "\n{} Main Simulation Program exited with error code: {}".format(
                PREFIX, result.returncode
            ),
            file=sys.stderr,
        )
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
