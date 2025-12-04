"""
CSP (Constraint Satisfaction Problem) engine for Minesweeper.

This module implements deterministic inference using constraint propagation.
It extracts constraints from revealed tiles and infers safe cells and mines.
"""

from typing import List, Tuple, Set, Dict
from collections import defaultdict
from solver.board import Board, TileState


class Constraint:
    """
    Represents a constraint from a revealed tile.
    
    A constraint states: sum of mines in unknown neighbors = required_mines
    """
    
    def __init__(self, center: Tuple[int, int], required_mines: int, 
                 unknown_neighbors: Set[Tuple[int, int]]):
        """
        Initialize a constraint.
        
        Args:
            center: (row, col) of the revealed tile that created this constraint
            required_mines: Number of mines that must be in unknown_neighbors
            unknown_neighbors: Set of (row, col) positions that are unknown
        """
        self.center = center
        self.required_mines = required_mines
        self.unknown_neighbors = unknown_neighbors.copy()
    
    def __repr__(self):
        return f"Constraint({self.center}, mines={self.required_mines}, unknowns={len(self.unknown_neighbors)})"


class CSPEngine:
    """
    CSP engine for deterministic inference in Minesweeper.
    
    Extracts constraints from revealed tiles and uses simple propagation
    to infer safe cells and mines.
    """
    
    def __init__(self):
        """Initialize the CSP engine."""
        self.constraints: List[Constraint] = []
        self.variable_to_constraints: Dict[Tuple[int, int], List[Constraint]] = defaultdict(list)
    
    def extract_constraints(self, board: Board) -> List[Constraint]:
        """
        Extract constraints from all revealed tiles on the board.
        
        For each revealed tile, create a constraint:
        sum(mines in unknown neighbors) = (number on tile - flagged neighbors)
        
        Args:
            board: The current board state
            
        Returns:
            List of Constraint objects
        """
        constraints = []
        self.variable_to_constraints.clear()
        
        # Iterate through all revealed cells
        for i, j in board.revealed_cells():
            # Get the number on this tile
            tile_value = board.get_tile(i, j)
            if tile_value < 0:  # Not a valid revealed tile
                continue
            
            # Get all neighbors
            neighbors = board.neighbors(i, j)
            
            # Count flagged neighbors
            flagged_count = sum(1 for ni, nj in neighbors if board.is_flagged(ni, nj))
            
            # Get unknown (unrevealed, unflagged) neighbors
            unknown_neighbors = {
                (ni, nj) for ni, nj in neighbors 
                if board.is_unknown(ni, nj)
            }
            
            # Calculate required mines in unknown neighbors
            required_mines = tile_value - flagged_count
            
            # Only create constraint if there are unknown neighbors
            if unknown_neighbors:
                constraint = Constraint((i, j), required_mines, unknown_neighbors)
                constraints.append(constraint)
                
                # Track which constraints involve each variable
                for var_pos in unknown_neighbors:
                    self.variable_to_constraints[var_pos].append(constraint)
        
        self.constraints = constraints
        return constraints
    
    def infer(self, board: Board) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
        """
        Perform deterministic inference to find safe cells and mines.
        
        Uses simple constraint propagation:
        1. If required_mines == 0, all unknowns are safe
        2. If required_mines == len(unknown_neighbors), all unknowns are mines
        
        Args:
            board: The current board state
            
        Returns:
            Tuple of (safe_cells, mine_cells) where each is a list of (row, col) tuples
        """
        # Extract constraints from current board state
        self.extract_constraints(board)
        
        safe_cells = []
        mine_cells = []
        
        # Check each constraint for deterministic inferences
        for constraint in self.constraints:
            if not constraint.unknown_neighbors:
                continue  # Constraint already satisfied
            
            # Rule 1: If required_mines == 0, all unknowns are safe
            if constraint.required_mines == 0:
                safe_cells.extend(constraint.unknown_neighbors)
            
            # Rule 2: If required_mines == len(unknown_neighbors), all unknowns are mines
            elif constraint.required_mines == len(constraint.unknown_neighbors):
                mine_cells.extend(constraint.unknown_neighbors)
        
        # Remove duplicates
        safe_cells = list(set(safe_cells))
        mine_cells = list(set(mine_cells))
        
        return safe_cells, mine_cells


def infer(board: Board) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
    """
    Convenience function to perform CSP inference on a board.
    
    Args:
        board: The current board state
        
    Returns:
        Tuple of (safe_cells, mine_cells) where each is a list of (row, col) tuples
    """
    engine = CSPEngine()
    return engine.infer(board)

