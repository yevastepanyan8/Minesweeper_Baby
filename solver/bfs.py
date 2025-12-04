"""
BFS (Breadth-First Search) module for revealing connected zero regions.

This module will be implemented by Person 3 to perform flood-fill
of connected zero tiles when a zero is revealed.
"""

from typing import Tuple
from solver.board import Board


def bfs_reveal(board: Board, start: Tuple[int, int]):
    """
    Reveal all connected zero tiles using BFS flood-fill.
    
    This is a placeholder for Person 3's implementation.
    For now, it just reveals the starting cell.
    
    Args:
        board: The board to modify
        start: (row, col) tuple of the starting position
    """
    from collections import deque
    
    # Verify the start cell is actually a zero
    if board.get_tile(start[0], start[1]) != 0:
        return
    
    # Queue for BFS - start with neighbors of the zero
    queue = deque()
    visited = set([start])
    
    # Add all neighbors of the starting zero
    neighbors = board.neighbors(start[0], start[1])
    for ni, nj in neighbors:
        if board.is_unknown(ni, nj):
            queue.append((ni, nj))
    
    # Process queue
    while queue:
        i, j = queue.popleft()
        
        if (i, j) in visited:
            continue
        
        visited.add((i, j))
        
        # Skip if already revealed or flagged
        if not board.is_unknown(i, j):
            continue
        
        # Reveal the cell
        if board.reveal(i, j):
            tile_value = board.get_tile(i, j)
            
            # If it's also a zero, add its neighbors to the queue
            if tile_value == 0:
                for ni, nj in board.neighbors(i, j):
                    if board.is_unknown(ni, nj) and (ni, nj) not in visited:
                        queue.append((ni, nj))

