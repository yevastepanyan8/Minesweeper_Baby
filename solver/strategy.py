"""
Main solver strategy that integrates CSP, probability, and BFS modules.

This module coordinates the decision-making loop, trying CSP inference first,
then falling back to probability-based choices when deterministic inference fails.
"""

from typing import Tuple, Optional, List
from solver.board import Board
from solver import csp
from solver import probability
from solver import bfs


def step(board: Board) -> Tuple[str, List[Tuple[int, int]]]:
    """
    Perform one step of the solver strategy.
    
    Strategy order:
    1. Try CSP deterministic inference (safe cells and mines)
    2. If no deterministic moves, use probability module
    3. Return the action and target cells
    
    Args:
        board: The current board state
        
    Returns:
        Tuple of (action_type, cells) where:
        - action_type: "reveal_safe", "flag_mines", or "guess"
        - cells: List of (row, col) tuples to act upon
    """
    # Step 1: Try CSP inference
    safe_cells, mine_cells = csp.infer(board)
    
    # Prioritize safe cells (reveal them)
    if safe_cells:
        return ("reveal_safe", safe_cells)
    
    # If we found mines, flag them
    if mine_cells:
        return ("flag_mines", mine_cells)
    
    # Step 2: No deterministic moves, use probability module
    # Person 2 will implement probability.choose_cell()
    cell = probability.choose_cell(board)
    
    if cell:
        return ("guess", [cell])
    
    # Fallback: return first unknown cell if probability module fails
    unknown = board.unknown_cells()
    if unknown:
        return ("guess", [next(iter(unknown))])
    
    # No moves available
    return ("none", [])


def solve_step(board: Board, action: str, cells: List[Tuple[int, int]]) -> bool:
    """
    Apply a solver action to the board.
    
    Args:
        board: The board to modify
        action: Action type ("reveal_safe", "flag_mines", "guess")
        cells: List of (row, col) tuples to act upon
        
    Returns:
        True if any action was successfully applied, False otherwise
    """
    success = False
    
    if action == "reveal_safe":
        for i, j in cells:
            if board.reveal(i, j):
                success = True
                # If revealed a zero, use BFS to reveal connected zeros
                if board.get_tile(i, j) == 0:
                    bfs.bfs_reveal(board, (i, j))
    
    elif action == "flag_mines":
        for i, j in cells:
            if board.flag(i, j):
                success = True
    
    elif action == "guess":
        for i, j in cells:
            if board.reveal(i, j):
                success = True
                # If revealed a zero, use BFS to reveal connected zeros
                if board.get_tile(i, j) == 0:
                    bfs.bfs_reveal(board, (i, j))
    
    return success

