"""
Probability-based cell selection module for Minesweeper.

This module implements probabilistic reasoning to select the safest cell
when deterministic CSP inference finds no new safe or mine cells.

Algorithm Overview:
-------------------
1. For each unknown cell, compute mine probability based on:
   - Local constraints from adjacent revealed tiles
   - Global probability (mines_left / unknown_cells)
   
2. Combine multiple constraints affecting the same cell using weighted average

3. Select the cell with lowest mine probability

Inspired by:
- mines.py: Constraint-based probability calculation
- JSMinesweeper: Local constraint aggregation and global fallback
- SelfSolvingMinesweeper: Simple probability rules

Design Choices:
--------------
- Uses local constraints first (more accurate)
- Falls back to global probability when no constraints
- Combines overlapping constraints with weighted average
- Avoids heavy SAT/backtracking for efficiency
"""

from collections import defaultdict
from typing import Dict, Optional, Tuple

from minesweeper.core.board import Board


def compute_local_probabilities(board: Board) -> Dict[Tuple[int, int], float]:
    """
    Compute mine probabilities for unknown cells based on local constraints.
    
    For each revealed tile with value n:
    - Count flagged neighbors: f
    - Count unknown neighbors: u
    - Remaining mines needed: r = n - f
    - Local probability for each unknown neighbor: r / u
    
    Args:
        board: The current board state
        
    Returns:
        Dictionary mapping (row, col) -> mine probability (0.0 to 1.0)
    """
    probabilities = {}
    constraint_counts = defaultdict(int)  # How many constraints affect each cell
    
    # Iterate through all revealed cells
    for i, j in board.revealed_cells():
        tile_value = board.get_tile(i, j)
        if tile_value < 0:  # Not a valid revealed tile
            continue
        
        # Get all neighbors
        neighbors = board.neighbors(i, j)
        
        # Count flagged and unknown neighbors
        flagged_count = sum(1 for ni, nj in neighbors if board.is_flagged(ni, nj))
        unknown_neighbors = [
            (ni, nj) for ni, nj in neighbors 
            if board.is_unknown(ni, nj)
        ]
        
        if not unknown_neighbors:
            continue  # No unknown neighbors, skip
        
        # Calculate remaining mines needed
        remaining_mines = tile_value - flagged_count
        
        # Rule A: If flagged_count == tile_value, all remaining are safe
        if remaining_mines == 0:
            for ni, nj in unknown_neighbors:
                probabilities[(ni, nj)] = 0.0
                constraint_counts[(ni, nj)] += 1
        
        # Rule B: If all unknowns must be mines
        elif remaining_mines == len(unknown_neighbors):
            for ni, nj in unknown_neighbors:
                probabilities[(ni, nj)] = 1.0
                constraint_counts[(ni, nj)] += 1
        
        # Rule C: Local probability = remaining_mines / unknown_neighbors
        else:
            local_prob = remaining_mines / len(unknown_neighbors)
            for ni, nj in unknown_neighbors:
                # If cell already has a probability, combine them
                if (ni, nj) in probabilities:
                    # Weighted average: (old * count + new) / (count + 1)
                    old_prob = probabilities[(ni, nj)]
                    old_count = constraint_counts[(ni, nj)]
                    probabilities[(ni, nj)] = (old_prob * old_count + local_prob) / (old_count + 1)
                    constraint_counts[(ni, nj)] += 1
                else:
                    probabilities[(ni, nj)] = local_prob
                    constraint_counts[(ni, nj)] = 1
    
    return probabilities


def compute_global_probability(board: Board) -> float:
    """
    Compute global mine probability based on remaining mines and unknown cells.
    
    Args:
        board: The current board state
        
    Returns:
        Global mine probability (0.0 to 1.0), or 0.0 if no unknown cells
    """
    unknown = board.unknown_cells()
    if not unknown:
        return 0.0
    
    # Prefer exact remaining-mine info when Board knows the total
    remaining_mines = board.remaining_mines()
    unknown_count = len(unknown)
    if remaining_mines is not None:
        if unknown_count > 0:
            return min(1.0, remaining_mines / unknown_count)
        return 0.0

    # Heuristic fallback when total mine count is unknown
    total_cells = board.rows * board.cols
    estimated_mine_density = 0.15  # 15% density as a reasonable prior
    estimated_total_mines = int(total_cells * estimated_mine_density)
    flagged_count = board.flagged_count()
    est_remaining = max(0, estimated_total_mines - flagged_count)

    if unknown_count > 0:
        return min(1.0, est_remaining / unknown_count)
    return 0.0


def compute_all_probabilities(board: Board) -> Dict[Tuple[int, int], float]:
    """
    Compute mine probabilities for all unknown cells.
    
    Combines local constraints with global fallback.
    
    Args:
        board: The current board state
        
    Returns:
        Dictionary mapping (row, col) -> mine probability (0.0 to 1.0)
    """
    # Get local probabilities from constraints
    local_probs = compute_local_probabilities(board)
    
    # Get global probability for fallback
    global_prob = compute_global_probability(board)
    
    # Get all unknown cells
    unknown = board.unknown_cells()
    
    # Build final probability map
    probabilities = {}
    for cell in unknown:
        if cell in local_probs:
            # Use local probability (from constraints)
            probabilities[cell] = local_probs[cell]
        else:
            # Rule D: Fall back to global probability
            probabilities[cell] = global_prob
    
    return probabilities


def choose_cell(board: Board) -> Optional[Tuple[int, int]]:
    """
    Choose the safest cell to reveal based on probability analysis.
    
    Selection rule:
    1. Choose cell with lowest mine probability
    2. If tie, prefer cell closer to center (heuristic)
    3. If no information, return first unknown cell
    
    Args:
        board: The current board state
        
    Returns:
        (row, col) tuple of the chosen cell, or None if no cells available
    """
    unknown = board.unknown_cells()
    if not unknown:
        return None
    
    # Compute probabilities for all unknown cells
    probabilities = compute_all_probabilities(board)
    
    if not probabilities:
        # No probabilities computed, return first unknown
        return next(iter(unknown))
    
    # Find minimum probability
    min_prob = min(probabilities.values())
    
    # Get all cells with minimum probability
    safest_cells = [cell for cell, prob in probabilities.items() if prob == min_prob]
    
    if len(safest_cells) == 1:
        return safest_cells[0]
    
    # Tie-breaking: prefer cell closer to center
    center_row = board.rows / 2.0
    center_col = board.cols / 2.0
    
    def distance_to_center(cell):
        r, c = cell
        return ((r - center_row) ** 2 + (c - center_col) ** 2) ** 0.5
    
    # Return cell closest to center
    return min(safest_cells, key=distance_to_center)


def debug_probabilities(board: Board) -> Dict[Tuple[int, int], float]:
    """
    Return a dictionary mapping each unknown cell to its mine probability.
    
    Useful for debugging and evaluation.
    
    Args:
        board: The current board state
        
    Returns:
        Dictionary mapping (row, col) -> mine probability (0.0 to 1.0)
    """
    return compute_all_probabilities(board)


def print_probability_map(board: Board):
    """
    Print a visual representation of probabilities for debugging.
    
    Args:
        board: The current board state
    """
    probs = debug_probabilities(board)
    
    print("\n" + "=" * (board.cols * 6 + 1))
    print("Probability Map (mine probability):")
    print("=" * (board.cols * 6 + 1))
    
    # Header
    print("   ", end="")
    for j in range(board.cols):
        print(f"{j:5}", end="")
    print()
    
    # Board with probabilities
    for i in range(board.rows):
        print(f"{i:2} ", end="")
        for j in range(board.cols):
            if board.is_revealed(i, j):
                val = board.get_tile(i, j)
                print(f" {val:4.0f}", end="")
            elif board.is_flagged(i, j):
                print("   F ", end="")
            elif (i, j) in probs:
                prob = probs[(i, j)]
                print(f"{prob:5.2f}", end="")
            else:
                print("  ?  ", end="")
        print()
    
    print("=" * (board.cols * 6 + 1))
    print()

