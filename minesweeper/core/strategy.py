"""
Main solver strategy that integrates CSP, probability, and BFS modules.

This module coordinates the decision-making loop, trying CSP inference first,
then falling back to probability-based choices when deterministic inference fails.
"""

from dataclasses import dataclass
from typing import List, Tuple

from minesweeper.core.board import Board
from minesweeper.expansion import bfs, dfs
from minesweeper.inference import csp, montecarlo, probability, sat


@dataclass(frozen=True)
class SolverConfig:
    """Toggles controlling which inference modules are used."""

    use_csp: bool = True
    use_sat: bool = True
    use_probability: bool = True
    use_monte_carlo: bool = True
    expansion: str = "bfs"  # or "dfs"


DEFAULT_CONFIG = SolverConfig()


def step(board: Board, config: SolverConfig = DEFAULT_CONFIG) -> Tuple[str, List[Tuple[int, int]]]:
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
    # Check if game is over - don't continue if mine was hit
    if board.game_over:
        return ("game_over", [])
    
    # Step 1: Try CSP inference if enabled
    safe_cells: List[Tuple[int, int]] = []
    mine_cells: List[Tuple[int, int]] = []

    if config.use_csp:
        safe_cells, mine_cells = csp.infer(board)

    # Prioritize safe cells (reveal them)
    if safe_cells:
        return ("reveal_safe", safe_cells)

    # If we found mines, flag them
    if mine_cells:
        return ("flag_mines", mine_cells)

    # Step 1.5: Try SAT-based reasoning for additional deterministic moves
    if config.use_sat:
        sat_safe, sat_mines = sat.infer(board)
        if sat_safe:
            return ("reveal_safe", sat_safe)
        if sat_mines:
            return ("flag_mines", sat_mines)
    
    # Step 2: Monte Carlo sampling for probabilistic inference
    if config.use_monte_carlo:
        mc_cell = montecarlo.choose_cell(board)
        if mc_cell:
            return ("guess", [mc_cell])

    # Step 3: No Monte Carlo info, use heuristic probability module
    cell = probability.choose_cell(board) if config.use_probability else None
    
    if cell:
        return ("guess", [cell])
    
    # Fallback: return first unknown cell if probability module fails
    unknown = board.unknown_cells()
    if unknown:
        return ("guess", [next(iter(unknown))])
    
    # No moves available
    return ("none", [])


def solve_step(
    board: Board,
    action: str,
    cells: List[Tuple[int, int]],
    config: SolverConfig = DEFAULT_CONFIG,
) -> bool:
    """
    Apply a solver action to the board.
    
    Args:
        board: The board to modify
        action: Action type ("reveal_safe", "flag_mines", "guess")
        cells: List of (row, col) tuples to act upon
        
    Returns:
        True if any action was successfully applied, False otherwise
    """
    # Check if game is over - don't continue if mine was hit
    if board.game_over:
        return False
    
    success = False
    
    expansion_fn = bfs.bfs_reveal if config.expansion == "bfs" else dfs.dfs_reveal

    if action == "reveal_safe":
        for i, j in cells:
            if board.game_over:
                break  # Stop immediately if mine was hit
            if board.reveal(i, j):
                success = True
                # Check if game over after reveal (mine was hit)
                if board.game_over:
                    break  # Stop immediately
                # If revealed a zero, use BFS to reveal connected zeros
                if board.get_tile(i, j) == 0:
                    expansion_fn(board, i, j)
    
    elif action == "flag_mines":
        for i, j in cells:
            if board.game_over:
                break
            if board.flag(i, j):
                success = True
    
    elif action == "guess":
        for i, j in cells:
            if board.game_over:
                break  # Stop immediately if mine was hit
            if board.reveal(i, j):
                success = True
                # Check if game over after reveal (mine was hit)
                if board.game_over:
                    break  # Stop immediately
                # If revealed a zero, use BFS to reveal connected zeros
                if board.get_tile(i, j) == 0:
                    expansion_fn(board, i, j)
    
    return success

