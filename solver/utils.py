"""
Utility functions for the Minesweeper solver.
"""

from typing import List, Tuple


def format_cells(cells: List[Tuple[int, int]]) -> str:
    """
    Format a list of cell coordinates as a string.
    
    Args:
        cells: List of (row, col) tuples
        
    Returns:
        Formatted string representation
    """
    if not cells:
        return "[]"
    return ", ".join(f"({r},{c})" for r, c in sorted(cells))

