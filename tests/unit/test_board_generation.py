"""Tests covering random/deferred mine generation behavior."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from minesweeper.core.board import Board


def test_first_click_generates_safe_zero_region():
    """First click should trigger lazy mine placement and yield a zero tile."""
    board = Board(6, 6, total_mines=6, rng_seed=123)
    board.reveal(3, 3)

    assert board.get_tile(3, 3) == 0, "First click should reveal a zero tile"

    for neighbor in board.neighbors(3, 3):
        # Revealing any neighbor should never hit a mine when the center is zero
        board.reveal(*neighbor)
        assert not board.game_over

    print("✓ First click safe zone honored")


def test_remaining_mines_tracks_flags():
    """Remaining mine estimate should decrease as flags are placed."""
    board = Board(5, 5, total_mines=10, rng_seed=7)
    assert board.total_mines() == 10
    assert board.remaining_mines() == 10

    board.flag(0, 0)
    board.flag(1, 1)

    assert board.remaining_mines() == 8
    board.unflag(1, 1)
    assert board.remaining_mines() == 9

    print("✓ Remaining mine tracking works correctly")


if __name__ == "__main__":
    test_first_click_generates_safe_zero_region()
    test_remaining_mines_tracks_flags()
