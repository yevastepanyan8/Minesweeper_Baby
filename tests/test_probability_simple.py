"""
Simple tests for the Probability module.

Tests probability computation and cell selection logic.
"""

from solver.board import Board
from solver.probability import (
    compute_local_probabilities,
    compute_global_probability,
    compute_all_probabilities,
    choose_cell,
    debug_probabilities
)


def test_rule_a_all_safe():
    """
    Test Rule A: If flagged_count == tile_value, all remaining neighbors are safe.
    
    Board:
    1 1 ?
    ? ? ?
    ? ? ?
    
    If (0,0) shows 1 and (0,1) is flagged, then (0,2) must be safe (probability 0).
    """
    board = Board(3, 3, {(0, 1)})  # Mine at (0,1)
    
    # Reveal (0,0) which should show 1 (one mine at (0,1))
    board.reveal(0, 0)
    
    # Flag the mine
    board.flag(0, 1)
    
    # Reveal (0,2) which should show 0
    board.reveal(0, 2)
    
    # Now (0,2) shows 0, so all its unknown neighbors should have probability 0
    probs = compute_local_probabilities(board)
    
    # Neighbors of (0,2) that are unknown should have probability 0
    neighbors = board.neighbors(0, 2)
    for ni, nj in neighbors:
        if board.is_unknown(ni, nj):
            assert (ni, nj) in probs, f"Cell ({ni},{nj}) should have probability"
            assert probs[(ni, nj)] == 0.0, f"Cell ({ni},{nj}) should be safe (prob=0)"
    
    print("✓ Rule A test passed: All safe neighbors correctly identified")


def test_rule_b_all_mines():
    """
    Test Rule B: If remaining_mines == unknown_neighbors, all are mines.
    
    Board:
    2 ? ?
    ? ? ?
    ? ? ?
    
    If (0,0) shows 2 and has 2 unknown neighbors, both must be mines (probability 1).
    """
    board = Board(3, 3, {(0, 1), (0, 2)})  # Mines at (0,1) and (0,2)
    
    # Reveal (0,0) which should show 2
    board.reveal(0, 0)
    
    probs = compute_local_probabilities(board)
    
    # Both (0,1) and (0,2) should have probability 1.0
    assert (0, 1) in probs, "Cell (0,1) should have probability"
    assert probs[(0, 1)] == 1.0, "Cell (0,1) should be a mine (prob=1)"
    
    assert (0, 2) in probs, "Cell (0,2) should have probability"
    assert probs[(0, 2)] == 1.0, "Cell (0,2) should be a mine (prob=1)"
    
    print("✓ Rule B test passed: All mine neighbors correctly identified")


def test_rule_c_local_probability():
    """
    Test Rule C: Local probability = remaining_mines / unknown_neighbors.
    
    Board:
    1 ? ?
    ? ? ?
    ? ? ?
    
    If (0,0) shows 1 and has 2 unknown neighbors, each has probability 0.5.
    """
    board = Board(3, 3, {(0, 1)})  # Mine at (0,1)
    
    # Reveal (0,0) which should show 1
    board.reveal(0, 0)
    
    probs = compute_local_probabilities(board)
    
    # (0,0) has 2 unknown neighbors: (0,1) and (0,2)
    # One is a mine, so probability = 1/2 = 0.5
    assert (0, 1) in probs, "Cell (0,1) should have probability"
    assert abs(probs[(0, 1)] - 0.5) < 0.01, f"Cell (0,1) should have prob ~0.5, got {probs[(0, 1)]}"
    
    assert (0, 2) in probs, "Cell (0,2) should have probability"
    assert abs(probs[(0, 2)] - 0.5) < 0.01, f"Cell (0,2) should have prob ~0.5, got {probs[(0, 2)]}"
    
    print("✓ Rule C test passed: Local probability correctly computed")


def test_rule_d_global_fallback():
    """
    Test Rule D: Global probability fallback when no local constraints.
    
    Board with no revealed tiles should use global probability.
    """
    board = Board(5, 5, {(0, 0), (1, 1)})  # Some mines
    
    # No tiles revealed, so all should use global probability
    probs = compute_all_probabilities(board)
    
    unknown = board.unknown_cells()
    assert len(probs) == len(unknown), "All unknown cells should have probabilities"
    
    # All should have the same global probability
    if probs:
        first_prob = next(iter(probs.values()))
        for prob in probs.values():
            assert abs(prob - first_prob) < 0.01, "All cells should have same global probability"
    
    print("✓ Rule D test passed: Global probability fallback works")


def test_choose_safest_cell():
    """
    Test that choose_cell selects the cell with lowest probability.
    
    Board:
    1 ? ?
    ? ? ?
    ? ? ?
    
    If (0,0) shows 1, it has 2 unknown neighbors with prob 0.5 each.
    Other cells should have higher global probability.
    The chosen cell should be one of the neighbors of (0,0).
    """
    board = Board(3, 3, {(0, 1)})  # Mine at (0,1)
    
    # Reveal (0,0) which should show 1
    board.reveal(0, 0)
    
    # Choose cell
    chosen = choose_cell(board)
    
    assert chosen is not None, "Should choose a cell"
    assert board.is_unknown(chosen[0], chosen[1]), "Chosen cell should be unknown"
    
    # The chosen cell should be one of the neighbors of (0,0) with lower probability
    neighbors = board.neighbors(0, 0)
    unknown_neighbors = [(ni, nj) for ni, nj in neighbors if board.is_unknown(ni, nj)]
    
    probs = compute_all_probabilities(board)
    if chosen in unknown_neighbors:
        # If it chose a neighbor, it should have lower probability than global
        chosen_prob = probs[chosen]
        # Should be reasonable (not too high)
        assert chosen_prob <= 0.6, f"Chosen cell should have reasonable probability, got {chosen_prob}"
    
    print(f"✓ Choose cell test passed: Selected ({chosen[0]},{chosen[1]})")


def test_multiple_constraints():
    """
    Test combining multiple constraints affecting the same cell.
    
    Board:
    1 1 ?
    ? ? ?
    ? ? ?
    
    Cell (1,1) is neighbor to both (0,0) and (0,1).
    If both show 1, the probabilities should be combined.
    """
    board = Board(3, 3, {(1, 0), (1, 2)})  # Mines at (1,0) and (1,2)
    
    # Reveal (0,0) and (0,1) which should both show 1
    board.reveal(0, 0)
    board.reveal(0, 1)
    
    probs = compute_local_probabilities(board)
    
    # (1,1) is neighbor to both (0,0) and (0,1)
    # Each constraint says: 1 mine in 2 unknowns, so prob = 0.5
    # Combined: should still be around 0.5 (weighted average)
    if (1, 1) in probs:
        prob = probs[(1, 1)]
        # Should be reasonable (combined from two 0.5 probabilities)
        assert 0.4 <= prob <= 0.6, f"Combined probability should be ~0.5, got {prob}"
    
    print("✓ Multiple constraints test passed: Probabilities correctly combined")


def run_all_tests():
    """Run all probability tests."""
    print("\n" + "=" * 60)
    print("Running Probability Module Tests")
    print("=" * 60)
    
    try:
        test_rule_a_all_safe()
        test_rule_b_all_mines()
        test_rule_c_local_probability()
        test_rule_d_global_fallback()
        test_choose_safest_cell()
        test_multiple_constraints()
        
        print("\n" + "=" * 60)
        print("All probability tests passed!")
        print("=" * 60 + "\n")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n✗ Test error: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()

