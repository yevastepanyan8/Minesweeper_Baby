"""
CSP (Constraint Satisfaction Problem) engine for Minesweeper.

This module implements deterministic inference using constraint propagation.
It extracts constraints from revealed tiles and infers safe cells and mines.
"""

from collections import defaultdict
from typing import Dict, List, Set, Tuple

from minesweeper.core.board import Board, TileState


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
        self.unknown_neighbors = unknown_neighbors.copy()
        # Clamp the requirement to the feasible range for this constraint
        self.required_mines = max(0, min(required_mines, len(self.unknown_neighbors)))
    
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
            if tile_value < 0 or tile_value == 9:  # Not a valid revealed tile (UNKNOWN/FLAGGED) or mine
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
            if required_mines < 0:
                required_mines = 0
            elif required_mines > len(unknown_neighbors):
                required_mines = len(unknown_neighbors)
            
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

        # Rule 3: Subset reasoning between overlapping constraints
        subset_safe, subset_mines = self._infer_from_subset_relationships()
        if subset_safe:
            safe_cells.extend(subset_safe)
        if subset_mines:
            mine_cells.extend(subset_mines)

        # Remove duplicates
        safe_cells = list(set(safe_cells))
        mine_cells = list(set(mine_cells))

        return safe_cells, mine_cells

    def _infer_from_subset_relationships(self) -> Tuple[Set[Tuple[int, int]], Set[Tuple[int, int]]]:
        """Use constraint subset relationships to deduce extra safe/mine cells."""
        safe: Set[Tuple[int, int]] = set()
        mines: Set[Tuple[int, int]] = set()

        constraints = [c for c in self.constraints if c.unknown_neighbors]
        count = len(constraints)
        for i in range(count):
            for j in range(i + 1, count):
                first = constraints[i]
                second = constraints[j]
                s, m = self._subset_implications(first, second)
                safe.update(s)
                mines.update(m)
                s, m = self._subset_implications(second, first)
                safe.update(s)
                mines.update(m)

        return safe, mines

    @staticmethod
    def _subset_implications(
        smaller: Constraint, larger: Constraint
    ) -> Tuple[Set[Tuple[int, int]], Set[Tuple[int, int]]]:
        """Infer cells when `smaller` is a subset of `larger`."""
        safe: Set[Tuple[int, int]] = set()
        mines: Set[Tuple[int, int]] = set()

        small_cells = smaller.unknown_neighbors
        large_cells = larger.unknown_neighbors
        if not small_cells or not large_cells or small_cells == large_cells:
            return safe, mines

        if small_cells.issubset(large_cells):
            extra_cells = large_cells - small_cells
            if not extra_cells:
                return safe, mines
            required_diff = larger.required_mines - smaller.required_mines
            if required_diff < 0 or required_diff > len(extra_cells):
                return safe, mines
            if required_diff == 0:
                safe.update(extra_cells)
            elif required_diff == len(extra_cells):
                mines.update(extra_cells)

        return safe, mines


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

