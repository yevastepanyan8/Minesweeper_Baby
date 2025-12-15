"""Minesweeper solver package with organized submodules."""

from .core.board import Board, TileState
from .core.strategy import DEFAULT_CONFIG, SolverConfig, solve_step, step
from .expansion import bfs
from .inference import csp, probability, sat
from .utils.formatting import format_cells

__all__ = [
    "Board",
    "TileState",
    "SolverConfig",
    "DEFAULT_CONFIG",
    "step",
    "solve_step",
    "bfs",
    "csp",
    "probability",
    "sat",
    "format_cells",
]

__version__ = "1.0.0"
