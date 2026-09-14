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

