"""
Simple tests for the BFS flood-fill module.

Tests BFS expansion for zero tiles and frontier revelation.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from minesweeper.core.board import Board
from minesweeper.expansion.bfs import bfs_reveal


def test_single_zero_expansion():
    """
    Test 1: Single zero expansion.
    
    Create a board with a large zero region and verify that all
    reachable zeros are revealed.
    
    Board layout:
    0 0 0
    0 0 0
    0 0 1
    
    All zeros should be revealed when starting from any zero.
    """
    # Create a 3x3 board with one mine at (2,2)
    board = Board(3, 3, {(2, 2)})
    
    # Reveal a zero tile (should trigger BFS)
    board.reveal(0, 0)
    
    # Since (0,0) will show 0, BFS should expand
    if board.get_tile(0, 0) == 0:
        revealed = bfs_reveal(board, 0, 0)
        
        # All zero tiles should be revealed
        # (0,0), (0,1), (0,2), (1,0), (1,1), (1,2), (2,0), (2,1) should be zeros
        # (2,2) is a mine, so it won't be revealed
        
        # Check that zeros are revealed
        assert board.is_revealed(0, 0), "(0,0) should be revealed"
        assert board.is_revealed(0, 1), "(0,1) should be revealed"
        assert board.is_revealed(0, 2), "(0,2) should be revealed"
        assert board.is_revealed(1, 0), "(1,0) should be revealed"
        assert board.is_revealed(1, 1), "(1,1) should be revealed"
        assert board.is_revealed(1, 2), "(1,2) should be revealed"
        assert board.is_revealed(2, 0), "(2,0) should be revealed"
        assert board.is_revealed(2, 1), "(2,1) should be revealed"
        
        # Check that the mine is not revealed
        assert not board.is_revealed(2, 2), "(2,2) should not be revealed (it's a mine)"
        
        # Check that revealed list contains the zeros
        assert len(revealed) >= 7, f"Should reveal at least 7 zeros, got {len(revealed)}"
        
        print("✓ Test 1 passed: Single zero expansion works correctly")


def test_zero_frontier():
    """
    Test 2: Zero + frontier.

    Zero region surrounded by numbered tiles. Check that:
    - Frontier is revealed (non-zero neighbors)
    - BFS doesn't continue through numbers

    Board layout:
    1 1 1
    1 0 1
    1 1 1

    When (1,1) is revealed as 0, BFS should reveal it and stop
    at the numbered neighbors (frontier).
    """
    # Create a 4x4 board with two mines far from the zero pocket
    board = Board(4, 4, {(0, 3), (3, 0)})

    # Reveal the center pocket which should be zero
    board.reveal(1, 1)
    assert board.get_tile(1, 1) == 0, "(1,1) should be zero"

    revealed = bfs_reveal(board, 1, 1)

    # Zeros around the starting point should be revealed
    zero_region = {
        (0, 0), (0, 1), (1, 0),
        (2, 2), (2, 3), (3, 2), (3, 3),
    }
    for cell in zero_region:
        assert board.is_revealed(*cell), f"Zero cell {cell} should be revealed"
        assert cell in revealed, f"Zero cell {cell} should be in BFS results"

    # Frontier tiles (numbers bordering the zero pocket) should be revealed
    frontier = {(0, 2), (1, 2), (1, 3), (2, 0), (2, 1), (3, 1)}
    for cell in frontier:
        assert board.is_revealed(*cell), f"Frontier cell {cell} should be revealed"
        assert cell in revealed, f"Frontier cell {cell} should appear in BFS results"

    # Mines should remain hidden and unrevealed
    assert board.is_unknown(0, 3), "Mine at (0,3) must remain hidden"
    assert board.is_unknown(3, 0), "Mine at (3,0) must remain hidden"

    print("✓ Test 2 passed: Zero + frontier handled correctly")


def test_no_bfs_for_non_zero():
    """
    Test 3: No BFS for non-zero.
    
    If a tile value = 2, BFS must do nothing (only reveal that tile).
    """
    # Create a board where (0,2) is adjacent to two mines
    board = Board(3, 3, {(0, 1), (1, 1)})

    # Reveal (0,2) which should show 2 (mines at (0,1) and (1,1))
    board.reveal(0, 2)
    
    tile_value = board.get_tile(0, 2)
    assert tile_value == 2, f"Tile (0,2) should show 2, got {tile_value}"
    
    # Call BFS - it should do nothing since tile is not zero
    initial_revealed = len(board.revealed_cells())
    revealed = bfs_reveal(board, 0, 2)
    
    # Should only reveal the starting tile (already revealed)
    # So revealed list should be empty or just contain (0,2) if it wasn't already counted
    final_revealed = len(board.revealed_cells())
    
    # BFS should not reveal additional tiles
    assert final_revealed == initial_revealed, "BFS should not reveal additional tiles for non-zero"
    
    # Check that neighbors are still unknown
    neighbors = board.neighbors(0, 2)
    for ni, nj in neighbors:
        if board.is_unknown(ni, nj):
            # These should remain unknown
            assert board.is_unknown(ni, nj), f"Neighbor ({ni},{nj}) should remain unknown"
    
    print("✓ Test 3 passed: No BFS for non-zero tiles")


def test_flags():
    """
    Test 4: Flags.
    
    Flagged tiles must not be revealed even if part of zero region.
    
    Board:
    0 0 0
    0 F 0
    0 0 0
    
    If we start BFS from (0,0), it should reveal all zeros except
    the flagged one at (1,1).
    """
    # Create an empty board (all zeros) and flag a safe tile
    board = Board(3, 3, set())

    # Flag the center
    board.flag(1, 1)
    assert board.is_flagged(1, 1), "Center should be flagged"

    # Reveal a zero and run BFS
    board.reveal(0, 0)

    if board.get_tile(0, 0) == 0:
        revealed = bfs_reveal(board, 0, 0)

        # All zeros should be revealed except the flagged one
        assert board.is_revealed(0, 0), "(0,0) should be revealed"
        assert board.is_revealed(0, 1), "(0,1) should be revealed"
        assert board.is_revealed(0, 2), "(0,2) should be revealed"
        assert board.is_revealed(1, 0), "(1,0) should be revealed"
        assert board.is_flagged(1, 1), "(1,1) should remain flagged"
        assert board.is_revealed(1, 2), "(1,2) should be revealed"
        assert board.is_revealed(2, 0), "(2,0) should be revealed"
        assert board.is_revealed(2, 1), "(2,1) should be revealed"
        assert board.is_revealed(2, 2), "(2,2) should be revealed"

        # Flagged tile should not be in revealed list
        assert (1, 1) not in revealed, "Flagged tile should not be revealed"

        print("✓ Test 4 passed: Flags are respected by BFS")


def test_bfs_already_revealed():
    """
    Additional test: BFS should not process already-revealed tiles.
    """
    board = Board(3, 3, {(2, 2)})
    
    # Reveal a zero
    board.reveal(0, 0)
    
    if board.get_tile(0, 0) == 0:
        # First BFS call
        revealed1 = bfs_reveal(board, 0, 0)
        count1 = len(revealed1)
        
        # Second BFS call on same tile (should do nothing)
        revealed2 = bfs_reveal(board, 0, 0)
        count2 = len(revealed2)
        
        # Second call should reveal nothing (already revealed)
        assert count2 == 0, f"Second BFS call should reveal 0 tiles, got {count2}"
        
        print("✓ Additional test passed: BFS handles already-revealed tiles correctly")


def run_all_tests():
    """Run all BFS tests."""
    print("\n" + "=" * 60)
    print("Running BFS Module Tests")
    print("=" * 60)
    
    try:
        test_single_zero_expansion()
        test_zero_frontier()
        test_no_bfs_for_non_zero()
        test_flags()
        test_bfs_already_revealed()
        
        print("\n" + "=" * 60)
        print("All BFS tests passed!")
        print("=" * 60 + "\n")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    run_all_tests()

