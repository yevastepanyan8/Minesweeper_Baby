"""
BFS (Breadth-First Search) module for revealing connected zero regions.

This module implements the classic Minesweeper flood-fill algorithm using BFS.
When a zero tile is revealed, this module automatically reveals all connected
zero tiles and their frontier (non-zero numbered neighbors).

Algorithm Overview:
------------------
BFS vs DFS:
- BFS uses a queue and processes tiles level-by-level
- DFS uses recursion/stack and goes deep first
- BFS is chosen because:
  1. More predictable memory usage (bounded by frontier width)
  2. Better for wide zero regions (common in Minesweeper)
  3. Easier to implement iteratively (no recursion limits)
  4. More efficient for typical Minesweeper board shapes

How Standard Minesweeper Flood-Fill Works:
-----------------------------------------
1. When a zero tile is clicked, it reveals itself
2. All adjacent zero tiles are automatically revealed
3. This continues recursively until no more zeros are found
4. The frontier (numbered tiles around zeros) are also revealed
5. This creates the characteristic "opening" effect in Minesweeper

Integration with CSP + Probability:
-----------------------------------
- CSP finds deterministic safe cells (including zeros)
- When CSP finds a zero, BFS expands it automatically
- This reveals more information for CSP to work with
- Probability module benefits from more revealed tiles (better constraints)
- BFS doesn't interfere with CSP/probability logic - it only reveals tiles

Design Choices:
--------------
- Iterative BFS (no recursion) for reliability
- Returns list of revealed cells for solver state tracking
- Only uses public Board API (no internal access)
- Handles edge cases: flags, boundaries, already-revealed tiles
"""

from collections import deque
from typing import List, Tuple

from minesweeper.core.board import Board


def bfs_reveal(board: Board, start_i: int, start_j: int) -> List[Tuple[int, int]]:
    """
    Reveal all connected zero tiles using BFS flood-fill.
    
    This implements the classic Minesweeper auto-reveal behavior:
    - Reveals all connected zero tiles
    - Reveals the frontier (non-zero numbered neighbors)
    - Stops at flagged tiles and boundaries
    
    Algorithm:
    1. If start tile is not zero, do nothing
    2. Use BFS queue starting from (start_i, start_j)
    3. For each zero tile:
       - Reveal it
       - Add its unknown neighbors to queue
    4. For each non-zero tile:
       - Reveal it (frontier)
       - Don't continue BFS through it
    
    Args:
        board: The board to modify
        start_i: Row index of the starting tile
        start_j: Column index of the starting tile
        
    Returns:
        List of (row, col) tuples for all newly revealed cells
    """
    revealed_cells = []
    
    # Check if game is over - don't continue if mine was hit
    if board.game_over:
        return revealed_cells
    
    # Check if start position is valid
    if not (0 <= start_i < board.rows and 0 <= start_j < board.cols):
        return revealed_cells
    
    # Check if start tile is flagged (don't reveal flagged tiles)
    if board.is_flagged(start_i, start_j):
        return revealed_cells
    
    # Get the value of the starting tile (may already be revealed)
    start_value = board.get_tile(start_i, start_j)
    
    # If it's not a zero, we're done (no BFS needed)
    if start_value != 0:
        return revealed_cells
    
    # If not already revealed, reveal it now
    if not board.is_revealed(start_i, start_j):
        if board.reveal(start_i, start_j):
            revealed_cells.append((start_i, start_j))
    
    # BFS queue: contains tiles to process
    # We start with neighbors of the initial zero
    queue = deque()
    visited = set([(start_i, start_j)])  # Track processed tiles
    
    # Add neighbors of the starting zero to the queue
    neighbors = board.neighbors(start_i, start_j)
    for ni, nj in neighbors:
        if board.is_unknown(ni, nj) and (ni, nj) not in visited:
            queue.append((ni, nj))
    
    # Process queue until empty
    while queue:
        # Check if game is over - stop immediately if mine was hit
        if board.game_over:
            break
        
        i, j = queue.popleft()
        
        # Skip if already visited
        if (i, j) in visited:
            continue
        
        visited.add((i, j))
        
        # Skip if already revealed or flagged
        if not board.is_unknown(i, j):
            continue
        
        # Reveal the tile
        if board.reveal(i, j):
            # Check if game over after reveal (mine was hit)
            if board.game_over:
                break
            
            revealed_cells.append((i, j))
            tile_value = board.get_tile(i, j)
            
            # Never expand into mines (value 9)
            if tile_value == 9:
                continue  # Skip this tile, don't add neighbors
            
            # If it's a zero, continue BFS by adding its neighbors
            if tile_value == 0:
                # Add all unknown neighbors to the queue
                for ni, nj in board.neighbors(i, j):
                    # Only add if:
                    # 1. It's unknown (not revealed, not flagged)
                    # 2. It's within bounds (handled by neighbors())
                    # 3. It hasn't been visited yet
                    if board.is_unknown(ni, nj) and (ni, nj) not in visited:
                        queue.append((ni, nj))
            # If it's not zero (frontier tile), we reveal it but don't continue BFS
            # This is the correct behavior - frontier tiles are revealed but
            # BFS doesn't propagate through them
    
    return revealed_cells


def bfs_reveal_tuple(board: Board, start: Tuple[int, int]) -> List[Tuple[int, int]]:
    """
    Convenience wrapper for bfs_reveal that accepts a tuple.
    
    This maintains backward compatibility with existing code that passes
    (i, j) as a tuple.
    
    Args:
        board: The board to modify
        start: (row, col) tuple of the starting position
        
    Returns:
        List of (row, col) tuples for all newly revealed cells
    """
    return bfs_reveal(board, start[0], start[1])
