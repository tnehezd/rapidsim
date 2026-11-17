import io
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock
import yaml

import h5py
import matplotlib
import numpy as np

matplotlib.use("Agg")

from rapidsim import postprocessing
from rapidsim import wrapper


RAPID_HEADER = "\n".join(
    (
        "=" * 74,
        "|| {:<68} ||".format("RAPID SIMULATION CORE"),
        "|| {:<68} ||".format("Version: 2.2.3"),
        "=" * 74,
    )
)


class RunGridTests(unittest.TestCase):
    @mock.patch("rapidsim.wrapper.subprocess.run")
    def test_reads_header_from_rapid_startup_banner(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            ["/fake/simulation", "--version"],
            1,
            stdout=RAPID_HEADER + "\nERROR [parseCLIOptions]\n",
        )

        self.assertEqual(
            wrapper._get_rapid_header("/fake/simulation"),
            RAPID_HEADER,
        )
        self.assertEqual(
            mock_run.call_args.args[0],
            ["/fake/simulation", "--version"],
        )

    def test_builds_supported_output_format_option(self):
        command = wrapper._build_command(
            {
                "output_parameters": {"output_format": "hdf5"},
                "log_parameters": {
                    "info_level": "info",
                    "disable_terminal_panels": True,
                },
            },
            "/fake/simulation",
        )

        self.assertEqual(command[1:], ["-v", "--output-format", "hdf5"])
        self.assertNotIn("-no_panels", command)

    def test_shared_deadzone_width_maps_to_both_boundaries(self):
        command = wrapper._build_command(
            {
                "deadzone_parameters": {
                    "deadzone_transition_width_mult": 1.5,
                }
            },
            "/fake/simulation",
        )

        self.assertEqual(
            command[1:],
            ["-drdzei", "1.5", "-drdzeo", "1.5"],
        )

    @mock.patch("rapidsim.wrapper._find_binary", return_value="/fake/simulation")
    @mock.patch("rapidsim.wrapper.subprocess.run")
    def test_run_redirects_process_output_to_log_file(
        self, mock_run, _mock_find_binary
    ):
        def fake_subprocess(command, **kwargs):
            kwargs["stdout"].write("RAPID output\n")
            return subprocess.CompletedProcess(command, 0)

        mock_run.side_effect = fake_subprocess
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "run.log")
            result = wrapper.run(
                {"log_parameters": {"disable_terminal_panels": True}},
                log_file=log_file,
            )

            with open(log_file, encoding="utf-8") as log_output:
                logged_output = log_output.read()

        self.assertEqual(result.returncode, 0)
        self.assertEqual(logged_output, "RAPID output\n")
        self.assertEqual(mock_run.call_args.kwargs["stderr"], subprocess.STDOUT)
        self.assertNotIn("-no_panels", mock_run.call_args.args[0])

    @mock.patch("rapidsim.wrapper._find_binary", return_value="/fake/simulation")
    @mock.patch("rapidsim.wrapper.subprocess.run")
    def test_run_displays_rapidsim_version(
        self, mock_run, _mock_find_binary
    ):
        mock_run.return_value = subprocess.CompletedProcess(["fake"], 0)
        output = io.StringIO()

        with redirect_stdout(output):
            wrapper.run({}, check=False)

        self.assertIn("RAPIDSIM PYTHON PACKAGE", output.getvalue())
        self.assertIn(
            "Version: {}".format(wrapper.get_version()),
            output.getvalue(),
        )
        self.assertIn(
            "|| {:^68} ||".format("RAPIDSIM PYTHON PACKAGE"),
            output.getvalue(),
        )
        self.assertIn(
            "|| {:^68} ||".format(
                "Version: {}".format(wrapper.get_version())
            ),
            output.getvalue(),
        )

    @mock.patch("rapidsim.wrapper.run_grid")
    def test_run_automatically_dispatches_multi_value_mapping_to_grid(
        self, mock_run_grid
    ):
        mock_run_grid.return_value = []
        config = {
            "disk_parameters": {"alpha_viscosity": [0.001, 0.01]},
            "grid_options": {"max_workers": 2},
        }

        result = wrapper.run(config, check=False)

        self.assertEqual(result, [])
        self.assertEqual(mock_run_grid.call_args.args[0], config)
        self.assertFalse(mock_run_grid.call_args.kwargs["check"])

    @mock.patch("rapidsim.wrapper.run_grid")
    def test_run_automatically_dispatches_multi_value_yaml_to_grid(
        self, mock_run_grid
    ):
        mock_run_grid.return_value = []
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "grid.yaml")
            with open(config_path, "w", encoding="utf-8") as config_file:
                yaml.safe_dump(
                    {
                        "disk_parameters": {
                            "alpha_viscosity": [0.001, 0.01],
                            "star_mass_msun": [1.0],
                        }
                    },
                    config_file,
                )

            result = wrapper.run(config_path)

        self.assertEqual(result, [])
        dispatched_config = mock_run_grid.call_args.args[0]
        self.assertEqual(
            dispatched_config["disk_parameters"]["alpha_viscosity"],
            [0.001, 0.01],
        )
        self.assertEqual(dispatched_config["disk_parameters"]["star_mass_msun"], 1.0)
        self.assertEqual(
            mock_run_grid.call_args.kwargs["_config_label"],
            os.path.abspath(config_path),
        )

    @mock.patch("rapidsim.wrapper._find_binary", return_value="/fake/simulation")
    @mock.patch("rapidsim.wrapper.subprocess.run")
    def test_run_treats_single_value_list_as_scalar(
        self, mock_run, _mock_find_binary
    ):
        mock_run.return_value = subprocess.CompletedProcess(["fake"], 0)

        result = wrapper.run(
            {"disk_parameters": {"alpha_viscosity": [0.01]}},
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn(
            ["-alpha_init", "0.01"],
            [
                mock_run.call_args.args[0][index:index + 2]
                for index in range(len(mock_run.call_args.args[0]) - 1)
            ],
        )

    @mock.patch("rapidsim.wrapper._find_binary", return_value="/fake/simulation")
    @mock.patch("rapidsim.wrapper.subprocess.run")
    def test_runs_grid_with_unique_output_directories(
        self, mock_run, _mock_find_binary
    ):
        def fake_subprocess(command, **kwargs):
            if command[-1] == "--version":
                return subprocess.CompletedProcess(
                    command,
                    1,
                    stdout=RAPID_HEADER + "\nERROR [parseCLIOptions]\n",
                )
            return subprocess.CompletedProcess(command, 0)

        mock_run.side_effect = fake_subprocess
        config = {
            "simulation_parameters": {"omp_num_threads": 1},
            "disk_parameters": {"alpha_viscosity": 0.01},
        }

        with tempfile.TemporaryDirectory() as output_dir:
            grid_dir = os.path.join(output_dir, "grid")
            results = wrapper.run_grid(
                config,
                {
                    "disk_parameters.alpha_viscosity": [0.001, 0.01],
                    "disk_parameters.sigma_profile_exponent": [-0.5, -1.0],
                },
                output_dir=grid_dir,
                max_workers=2,
            )

        self.assertEqual(len(results), 4)
        self.assertEqual(len({result.output_dir for result in results}), 4)
        self.assertEqual(mock_run.call_count, 5)
        self.assertTrue(
            all(
                os.path.basename(result.output_dir).startswith("run_")
                for result in results
            )
        )

    @mock.patch("rapidsim.wrapper._get_rapid_header", return_value=RAPID_HEADER)
    @mock.patch("rapidsim.wrapper.run")
    def test_reads_paired_grid_and_options_from_yaml(
        self, mock_run, _mock_get_rapid_header
    ):
        mock_run.side_effect = lambda config, output_dir, check, log_file=None: (
            subprocess.CompletedProcess(["fake"], 0)
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = os.path.join(temp_dir, "grid_output")
            config_path = os.path.join(temp_dir, "grid.yaml")
            with open(config_path, "w", encoding="utf-8") as config_file:
                yaml.safe_dump(
                    {
                        "simulation_parameters": {"enable_gas_evolution": True},
                        "deadzone_parameters": {
                            "deadzone_inner_transition_width_mult": [1.0, 1.5],
                            "deadzone_outer_transition_width_mult": [2.0, 2.5],
                        },
                        "grid_options": {
                            "output_directory": output_dir,
                            "max_workers": 2,
                        },
                    },
                    config_file,
                )

            output = io.StringIO()
            with redirect_stdout(output):
                results = wrapper.run_grid(config_path, mode="paired")

        self.assertEqual(len(results), 2)
        self.assertIn("RAPIDSIM PYTHON PACKAGE", output.getvalue())
        self.assertIn(
            "Version: {}".format(wrapper.get_version()),
            output.getvalue(),
        )
        self.assertIn("RAPID SIMULATION CORE", output.getvalue())
        self.assertIn("Version: 2.2.3", output.getvalue())
        self.assertIn("RAPIDSIM PARAMETER GRID", output.getvalue())
        self.assertIn("Runs:", output.getvalue())
        self.assertNotIn("Combination rule:", output.getvalue())
        self.assertNotIn("all combinations", output.getvalue())
        self.assertIn("grid.yaml", output.getvalue())
        self.assertIn("Parallel workers:", output.getvalue())
        self.assertIn("Gas evolution:", output.getvalue())
        self.assertIn("[True]", output.getvalue())
        self.assertNotIn("GRID PARAMETERS", output.getvalue())
        self.assertLess(
            output.getvalue().index("DEAD-ZONE PARAMETERS"),
            output.getvalue().index("Inner transition width multiplier:"),
        )
        self.assertIn("=" * 74, output.getvalue())
        self.assertTrue(
            all(
                len(line) == 74
                for line in output.getvalue().splitlines()
                if line.startswith("||")
            )
        )
        self.assertIn("[RUNNING 01/02] run_0001", output.getvalue())
        self.assertIn(
            "deadzone_parameters.deadzone_inner_transition_width_mult = 1.0",
            output.getvalue(),
        )
        self.assertIn("[1.0, 1.5]", output.getvalue())
        self.assertEqual(mock_run.call_count, 2)
        self.assertEqual(len({result.output_dir for result in results}), 2)
        self.assertTrue(all(result.log_file for result in results))
        self.assertTrue(
            all(
                call.kwargs["log_file"].endswith(".log")
                for call in mock_run.call_args_list
            )
        )
        generated_configs = [call.args[0] for call in mock_run.call_args_list]
        self.assertEqual(
            {
                (
                    config["deadzone_parameters"][
                        "deadzone_inner_transition_width_mult"
                    ],
                    config["deadzone_parameters"][
                        "deadzone_outer_transition_width_mult"
                    ],
                )
                for config in generated_configs
            },
            {(1.0, 2.0), (1.5, 2.5)},
        )
        self.assertTrue(
            all(
                config["simulation_parameters"]["enable_gas_evolution"]
                for config in generated_configs
            )
        )

    @mock.patch("rapidsim.wrapper._get_rapid_header", return_value=RAPID_HEADER)
    @mock.patch("rapidsim.wrapper.run")
    def test_grid_check_false_returns_failed_results(
        self, mock_run, _mock_get_rapid_header
    ):
        mock_run.return_value = subprocess.CompletedProcess(["fake"], 2)
        with tempfile.TemporaryDirectory() as temp_dir:
            results = wrapper.run_grid(
                {"disk_parameters": {"alpha_viscosity": 0.01}},
                {"disk_parameters.alpha_viscosity": [0.01]},
                output_dir=os.path.join(temp_dir, "grid"),
                max_workers=1,
                check=False,
            )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].process.returncode, 2)

    @mock.patch("rapidsim.wrapper.run")
    def test_cli_returns_success_for_successful_grid(self, mock_run):
        mock_run.return_value = [
            wrapper.GridRunResult(
                {"disk_parameters.alpha_viscosity": 0.01},
                "run_0001",
                subprocess.CompletedProcess(["fake"], 0),
            )
        ]
        output = io.StringIO()
        with redirect_stdout(output):
            return_code = wrapper.main(["--config", "grid.yaml"])

        self.assertEqual(return_code, 0)
        self.assertIn("Grid simulation completed successfully (1 runs).", output.getvalue())

    @mock.patch("rapidsim.wrapper.run")
    def test_cli_returns_failure_for_failed_grid(self, mock_run):
        mock_run.return_value = [
            wrapper.GridRunResult(
                {"disk_parameters.alpha_viscosity": 0.01},
                "run_0001",
                subprocess.CompletedProcess(["fake"], 3),
            )
        ]
        error_output = io.StringIO()
        with redirect_stderr(error_output):
            return_code = wrapper.main(["--config", "grid.yaml"])

        self.assertEqual(return_code, 3)
        self.assertIn("Grid simulation had 1 failed run(s)", error_output.getvalue())

    @mock.patch("rapidsim.wrapper._get_rapid_header", return_value=RAPID_HEADER)
    @mock.patch("rapidsim.wrapper.run")
    def test_shared_width_grid_crosses_with_other_inline_lists(
        self, mock_run, _mock_get_rapid_header
    ):
        mock_run.side_effect = lambda config, output_dir, check, log_file=None: (
            subprocess.CompletedProcess(["fake"], 0)
        )
        config = {
            "disk_parameters": {
                "sigma_profile_exponent": [-0.5, 1.0, 1.5],
            },
            "deadzone_parameters": {
                "deadzone_transition_width_mult": [1.0, 1.5],
            },
            "grid_options": {"output_directory": "unused"},
        }

        with tempfile.TemporaryDirectory() as output_dir:
            config["grid_options"]["output_directory"] = os.path.join(
                output_dir, "grid"
            )
            results = wrapper.run_grid(config)

        self.assertEqual(len(results), 6)
        generated_configs = [call.args[0] for call in mock_run.call_args_list]
        self.assertEqual(
            {
                (
                    config["deadzone_parameters"][
                        "deadzone_inner_transition_width_mult"
                    ],
                    config["deadzone_parameters"][
                        "deadzone_outer_transition_width_mult"
                    ],
                    config["disk_parameters"]["sigma_profile_exponent"],
                )
                for config in generated_configs
            },
            {
                (width, width, exponent)
                for width in (1.0, 1.5)
                for exponent in (-0.5, 1.0, 1.5)
            },
        )

    @mock.patch("rapidsim.wrapper._get_rapid_header", return_value=RAPID_HEADER)
    @mock.patch("rapidsim.wrapper.run")
    def test_existing_output_directory_uses_next_numbered_name(
        self, mock_run, _mock_get_rapid_header
    ):
        mock_run.return_value = subprocess.CompletedProcess(["fake"], 0)
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = os.path.join(temp_dir, "grid")
            os.makedirs(output_dir)
            os.makedirs(output_dir + "_0001")

            results = wrapper.run_grid(
                {"disk_parameters": {"alpha_viscosity": 0.01}},
                {"disk_parameters.alpha_viscosity": [0.01]},
                output_dir=output_dir,
                max_workers=1,
            )

        self.assertEqual(
            results[0].output_dir,
            os.path.join(temp_dir, "grid_0002", "run_0001"),
        )
        self.assertTrue(
            results[0].log_file.startswith(os.path.join(temp_dir, "grid_0002"))
        )


class PostprocessingTests(unittest.TestCase):
    def _write_snapshot(self, path, time_value):
        with h5py.File(path, "w") as snapshot_file:
            gas = snapshot_file.create_group("gas_grid")
            gas.create_dataset("radial_grid", data=np.array([1.0, 10.0, 100.0]))
            gas.create_dataset(
                "surface_density", data=np.array([1e-4, 1e-5, 1e-6])
            )
            frame = snapshot_file.create_group("frame")
            frame.create_dataset("time", data=np.array([time_value]))

    def test_loads_plots_and_animates_snapshots(self):
        with tempfile.TemporaryDirectory() as output_dir:
            logs_dir = os.path.join(output_dir, "LOGS")
            os.makedirs(logs_dir)
            for time_value in (0.0, 10.0):
                path = os.path.join(
                    logs_dir, "snapshot_{:08d}.h5".format(int(time_value))
                )
                self._write_snapshot(path, time_value)

            snapshot_path = os.path.join(logs_dir, "snapshot_00000000.h5")
            snapshot = postprocessing.load_snapshot(snapshot_path)
            self.assertEqual(snapshot.time, 0.0)
            self.assertEqual(snapshot.surface_density["gas"].shape, (3,))

            figure, _ = postprocessing.plot_snapshot(snapshot_path)
            animation = postprocessing.animate_snapshots(output_dir)
            animation._func(0)
            animation.save(os.path.join(output_dir, "animation.gif"), writer="pillow")
            postprocessing.plt.close(figure)
            postprocessing.plt.close(animation._fig)


if __name__ == "__main__":
    unittest.main()
