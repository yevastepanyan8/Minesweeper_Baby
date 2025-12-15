"""Tests for the SAT-style inference helper."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from minesweeper.core.board import Board
from minesweeper.inference import sat


def setup_sat_board():
    """Create a board where SAT reasoning adds information beyond CSP mines."""
    board = Board(3, 3, {(0, 1), (1, 2)})
    # Reveal a plus-shaped pattern around the unknown frontier
    board.reveal(0, 0)
    board.reveal(0, 2)
    board.reveal(2, 0)
    board.reveal(2, 2)
    return board


def test_sat_deduces_mines_and_safe_cells():
    """SAT enumeration should determine both safe and mined locations."""
    board = setup_sat_board()
    safe, mines = sat.infer(board)

    assert set(safe) >= {(1, 0), (1, 1), (2, 1)}
    assert set(mines) >= {(0, 1), (1, 2)}

    print("✓ SAT inference deduced guaranteed cells correctly")


def test_sat_handles_no_constraints():
    """If there are no revealed numbers, SAT should return nothing."""
    board = Board(3, 3, {(0, 0)})
    safe, mines = sat.infer(board)
    assert safe == [] and mines == []
    print("✓ SAT inference gracefully handles empty constraint sets")


if __name__ == "__main__":
    test_sat_deduces_mines_and_safe_cells()
    test_sat_handles_no_constraints()
