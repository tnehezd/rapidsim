# rapidsim/__init__.py
from .wrapper import GridRunError, GridRunResult, get_version, main, run, run_grid

__version__ = get_version()

__all__ = [
    "__version__",
    "GridRunError",
    "GridRunResult",
    "main",
    "run",
    "run_grid",
]