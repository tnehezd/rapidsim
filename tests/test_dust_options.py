import copy
import math
import os
import tempfile
import unittest
from unittest import mock

from rapidsim import wrapper


class DustOptionsTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "simulation_parameters": {
                "enable_dust_drift": True,
                "enable_dust_growth": False,
                "enable_two_dust_populations": False,
            },
            "dust_parameters": {"constant_stokes_number": 0.1},
        }

    def test_constant_stokes_command(self):
        command = wrapper._build_command(self.config, "/fake/simulation")
        self.assertEqual(command[command.index("-stokes") + 1], "0.1")
        self.assertNotIn("-largesize", command)

    def test_invalid_stokes(self):
        for value in (0, -1, True, None, "0.1", math.nan, math.inf):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.config["dust_parameters"]["constant_stokes_number"] = value
                wrapper._build_command(self.config, "/fake/simulation")

    def test_incompatible_modes(self):
        for key, value in (
            ("enable_dust_drift", False),
            ("enable_dust_growth", True),
            ("enable_two_dust_populations", True),
        ):
            config = copy.deepcopy(self.config)
            config["simulation_parameters"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                wrapper._build_command(config, "/fake/simulation")
        for key in ("enable_dust_growth",):
            config = copy.deepcopy(self.config)
            del config["simulation_parameters"][key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                wrapper._build_command(config, "/fake/simulation")

    def test_incompatible_size_and_input(self):
        for section, key, value in (
            ("dust_parameters", "one_size_particle_value_cm", 0.1),
            ("dust_parameters", "large_size_particle_value_cm", 0.1),
            ("disk_parameters", "input_file_path", "profile.dat"),
            ("simulation_parameters", "test_mode", "mass_test"),
        ):
            config = copy.deepcopy(self.config)
            config.setdefault(section, {})[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                wrapper._build_command(config, "/fake/simulation")

    def test_fixed_size_and_fragmentation_mapping(self):
        for key in ("one_size_particle_value_cm", "large_size_particle_value_cm"):
            command = wrapper._build_command({
                "simulation_parameters": {
                    "fragmentation_velocity": 500.0,
                    "fragmentation_factor": 0.37,
                },
                "dust_parameters": {key: 0.1},
            }, "/fake/simulation")
            self.assertEqual(command[1:], [
                "-ufrag", "500.0", "-ffrag", "0.37", "-largesize", "0.1",
                "-twopop", "0", "-ratio", "1",
            ])
            self.assertNotIn("-stokes", command)

    def test_two_population_disabled_and_default_off(self):
        for key in ("enable_two_dust_populations", "population_one_mass_ratio",
                    "micro_particle_size_cm"):
            self.assertNotIn(key, wrapper.YAML_TO_C_MAPPING)
        for section in ("simulation_parameters", "dust_parameters"):
            with self.subTest(section=section), self.assertRaisesRegex(ValueError, "temporarily disabled"):
                wrapper._build_command({section: {"enable_two_dust_populations": True}},
                                       "/fake/simulation")
        with self.assertRaisesRegex(ValueError, "mass_ratio must be 1"):
            wrapper._build_command({"dust_parameters": {"population_one_mass_ratio": .85}},
                                   "/fake/simulation")
        with self.assertRaisesRegex(ValueError, "micro_particle_size_cm is unavailable"):
            wrapper._build_command({"dust_parameters": {"micro_particle_size_cm": 1e-4}},
                                   "/fake/simulation")
        config = copy.deepcopy(self.config)
        del config["simulation_parameters"]["enable_two_dust_populations"]
        command = wrapper._build_command(config, "/fake/simulation")
        self.assertEqual(command[command.index("-twopop") + 1], "0")
        self.assertEqual(command[command.index("-ratio") + 1], "1")

    @mock.patch("rapidsim.wrapper._find_binary", return_value="/fake/simulation")
    @mock.patch("rapidsim.wrapper.subprocess.run")
    def test_stokes_parameter_grid(self, run, find_binary):
        run.return_value = mock.Mock(returncode=0)
        with tempfile.TemporaryDirectory() as temp_dir, \
             mock.patch("rapidsim.wrapper._get_rapid_header", return_value="RAPID"), \
             mock.patch("builtins.print"):
            results = wrapper.run_grid(
                self.config,
                {"dust_parameters.constant_stokes_number": [0.1, 0.2]},
                output_dir=os.path.join(temp_dir, "grid"),
            )
        self.assertEqual(len(results), 2)
        commands = [call.args[0] for call in run.call_args_list]
        values = [command[command.index("-stokes") + 1] for command in commands]
        self.assertEqual(sorted(values), ["0.1", "0.2"])


if __name__ == "__main__":
    unittest.main()
