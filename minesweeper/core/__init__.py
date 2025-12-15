"""Core gameplay elements (board state, solver strategy)."""

from .board import Board, TileState
from .strategy import step, solve_step

__all__ = ["Board", "TileState", "step", "solve_step"]
