from setuptools import setup
from setuptools.command.build_py import build_py

import os
import shutil
import subprocess


class CustomBuildPy(build_py):

    def run(self):
        # Paths relative to the rapidsim repository root
        rapid_dir = os.path.join("external", "RAPID")
        rapid_bin = os.path.join(rapid_dir, "bin", "simulation")

        package_data_dir = os.path.join("rapidsim", "data")
        package_bin = os.path.join(package_data_dir, "simulation")

        if not os.path.isdir(rapid_dir):
            raise RuntimeError(
                "[SETUP] RAPID submodule not found at "
                f"{rapid_dir}. Initialize it with:\n"
                "    git submodule update --init --recursive"
            )

        print("[SETUP] Compiling RAPID simulation engine...")
        print(f"[SETUP] RAPID source: {rapid_dir}")

        # Build RAPID inside the submodule
        subprocess.check_call(
            ["make", "clean"],
            cwd=rapid_dir,
        )

        subprocess.check_call(
            ["make", "all"],
            cwd=rapid_dir,
        )

        # Verify that the expected executable was created
        if not os.path.exists(rapid_bin):
            raise RuntimeError(
                "[SETUP] RAPID build succeeded, but the simulation binary "
                f"was not found at {rapid_bin}"
            )

        # Bundle the executable into the Python package
        os.makedirs(package_data_dir, exist_ok=True)

        shutil.copy2(rapid_bin, package_bin)

        print(
            f"[SETUP] Successfully bundled RAPID binary to {package_bin}"
        )

        super().run()


cmdclass = {
    "build_py": CustomBuildPy,
}


# Make the wheel non-pure because it contains a compiled executable.
try:
    from wheel.bdist_wheel import bdist_wheel

    class BinaryBdistWheel(bdist_wheel):

        def finalize_options(self):
            super().finalize_options()
            self.root_is_pure = False

    cmdclass["bdist_wheel"] = BinaryBdistWheel

except ImportError:
    pass


setup(
    name="rapidsim",
    version="1.0.7",
    packages=["rapidsim"],
    package_data={
        "rapidsim": [
            "data/simulation",
        ],
    },
    include_package_data=True,
    cmdclass=cmdclass,
)