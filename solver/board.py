"""
Board representation and internal game state model.

This module provides the Board class which maintains the internal state
of a Minesweeper game, including tile states, mine locations, and game logic.
"""

from enum import IntEnum
from typing import List, Tuple, Set, Optional


class TileState(IntEnum):
    """Represents the state of a tile."""
    UNKNOWN = -1
    SAFE = 0
    FLAGGED = -2
    # Revealed tiles have values 0-8 representing adjacent mine count


class Board:
    """
    Internal representation of a Minesweeper board.
    
    The board maintains:
    - Tile states (UNKNOWN, SAFE, FLAGGED, or revealed with mine count)
    - Internal mine locations (for simulation/testing)
    - Game state tracking
    """
    
    def __init__(self, rows: int, cols: int, bombs: Optional[Set[Tuple[int, int]]] = None):
        """
        Initialize a new board.
        
        Args:
            rows: Number of rows in the board
            cols: Number of columns in the board
            bombs: Optional set of (row, col) tuples representing mine locations.
                   If None, mines are not set (for loading from file).
        """
        self.rows = rows
        self.cols = cols
        self._board = [[TileState.UNKNOWN for _ in range(cols)] for _ in range(rows)]
        self._bombs = bombs if bombs is not None else set()
        self._revealed_count = 0
        self._flagged_count = 0
        
    def neighbors(self, i: int, j: int) -> List[Tuple[int, int]]:
        """
        Get all valid neighbor coordinates for a cell.
        
        Args:
            i: Row index
            j: Column index
            
        Returns:
            List of (row, col) tuples for valid neighbors
        """
        neighbors = []
        for di in [-1, 0, 1]:
            for dj in [-1, 0, 1]:
                if di == 0 and dj == 0:
                    continue
                ni, nj = i + di, j + dj
                if 0 <= ni < self.rows and 0 <= nj < self.cols:
                    neighbors.append((ni, nj))
        return neighbors
    
    def reveal(self, i: int, j: int) -> bool:
        """
        Reveal a tile at position (i, j).
        
        Args:
            i: Row index
            j: Column index
            
        Returns:
            True if the tile was successfully revealed, False if already revealed/flagged
        """
        if not (0 <= i < self.rows and 0 <= j < self.cols):
            return False
            
        if self._board[i][j] != TileState.UNKNOWN:
            return False  # Already revealed or flagged
        
        # Check if it's a bomb (for simulation)
        if (i, j) in self._bombs:
            # Mark as a special value to indicate it's a bomb (we'll use a high number)
            # This shouldn't happen in normal solving, but we handle it gracefully
            self._board[i][j] = 9  # Special value for bomb (not a valid mine count)
            self._revealed_count += 1
            return True
        
        # Count adjacent mines
        count = self.count_adjacent_mines(i, j)
        self._board[i][j] = count
        self._revealed_count += 1
        return True
    
    def flag(self, i: int, j: int) -> bool:
        """
        Flag a tile as a potential mine.
        
        Args:
            i: Row index
            j: Column index
            
        Returns:
            True if the tile was successfully flagged, False otherwise
        """
        if not (0 <= i < self.rows and 0 <= j < self.cols):
            return False
            
        if self._board[i][j] != TileState.UNKNOWN:
            return False  # Already revealed or flagged
        
        self._board[i][j] = TileState.FLAGGED
        self._flagged_count += 1
        return True
    
    def unflag(self, i: int, j: int) -> bool:
        """
        Unflag a tile.
        
        Args:
            i: Row index
            j: Column index
            
        Returns:
            True if the tile was successfully unflagged, False otherwise
        """
        if not (0 <= i < self.rows and 0 <= j < self.cols):
            return False
            
        if self._board[i][j] != TileState.FLAGGED:
            return False
        
        self._board[i][j] = TileState.UNKNOWN
        self._flagged_count -= 1
        return True
    
    def count_adjacent_mines(self, i: int, j: int) -> int:
        """
        Count the number of adjacent mines for a cell.
        Used for simulation/testing when mines are known.
        
        Args:
            i: Row index
            j: Column index
            
        Returns:
            Number of adjacent mines
        """
        count = 0
        for ni, nj in self.neighbors(i, j):
            if (ni, nj) in self._bombs:
                count += 1
        return count
    
    def get_tile(self, i: int, j: int) -> int:
        """
        Get the state/value of a tile.
        
        Returns:
            TileState.UNKNOWN (-1), TileState.FLAGGED (-2), TileState.SAFE (0),
            or a number 0-8 for revealed tiles with mine count
        """
        if not (0 <= i < self.rows and 0 <= j < self.cols):
            return TileState.UNKNOWN
        return self._board[i][j]
    
    def is_revealed(self, i: int, j: int) -> bool:
        """Check if a tile is revealed."""
        val = self.get_tile(i, j)
        return val >= 0 and val != TileState.FLAGGED
    
    def is_flagged(self, i: int, j: int) -> bool:
        """Check if a tile is flagged."""
        return self.get_tile(i, j) == TileState.FLAGGED
    
    def is_unknown(self, i: int, j: int) -> bool:
        """Check if a tile is unknown."""
        return self.get_tile(i, j) == TileState.UNKNOWN
    
    def unknown_cells(self) -> Set[Tuple[int, int]]:
        """
        Get all unknown (unrevealed, unflagged) cells.
        
        Returns:
            Set of (row, col) tuples for unknown cells
        """
        unknown = set()
        for i in range(self.rows):
            for j in range(self.cols):
                if self.is_unknown(i, j):
                    unknown.add((i, j))
        return unknown
    
    def revealed_cells(self) -> Set[Tuple[int, int]]:
        """
        Get all revealed cells.
        
        Returns:
            Set of (row, col) tuples for revealed cells
        """
        revealed = set()
        for i in range(self.rows):
            for j in range(self.cols):
                if self.is_revealed(i, j):
                    revealed.add((i, j))
        return revealed
    
    def is_finished(self) -> bool:
        """
        Check if the game is finished (all non-mine cells revealed).
        
        Returns:
            True if all safe cells are revealed
        """
        total_cells = self.rows * self.cols
        return self._revealed_count + len(self._bombs) == total_cells
    
    def reveal_zero_region(self, i: int, j: int):
        """
        Reveal all connected zero tiles using BFS.
        
        This is a placeholder for Person 3's BFS implementation.
        For now, it just reveals the single cell.
        
        Args:
            i: Row index
            j: Column index
        """
        # Person 3 will implement BFS flood-fill here
        # For now, just reveal the cell
        self.reveal(i, j)
    
    def print_board_raw(self):
        """Print the raw board state for debugging."""
        print("Raw Board State:")
        print(f"Rows: {self.rows}, Cols: {self.cols}")
        print(f"Bombs: {self._bombs}")
        print("Board:")
        for i in range(self.rows):
            row = []
            for j in range(self.cols):
                val = self._board[i][j]
                if val == TileState.UNKNOWN:
                    row.append("?")
                elif val == TileState.FLAGGED:
                    row.append("F")
                elif val >= 0:
                    row.append(str(val))
                else:
                    row.append(".")
            print(" ".join(row))
    
    def print_solver_view(self):
        """
        Print the board in ASCII format as the solver sees it.
        Shows revealed numbers, flags, and unknown tiles.
        """
        print("\n" + "=" * (self.cols * 2 + 1))
        print("Solver View:")
        print("=" * (self.cols * 2 + 1))
        
        # Header
        print("   ", end="")
        for j in range(self.cols):
            print(f"{j:2}", end="")
        print()
        
        # Board
        for i in range(self.rows):
            print(f"{i:2} ", end="")
            for j in range(self.cols):
                val = self.get_tile(i, j)
                if val == TileState.UNKNOWN:
                    print(" ?", end="")
                elif val == TileState.FLAGGED:
                    print(" F", end="")
                elif val >= 0:
                    print(f" {val}", end="")
                else:
                    print(" .", end="")
            print()
        
        print("=" * (self.cols * 2 + 1))
        print(f"Revealed: {self._revealed_count}, Flagged: {self._flagged_count}")
        print()
    
    @staticmethod
    def load_from_file(filepath: str) -> 'Board':
        """
        Load a board from a text file.
        
        File format:
        First line: rows cols num_bombs
        Following lines: board representation
        - '.' or ' ' for empty/safe cells
        - '*' or 'M' for mines
        - Numbers 0-8 for revealed cells with mine count
        
        Args:
            filepath: Path to the board file
            
        Returns:
            A Board instance with the loaded configuration
        """
        with open(filepath, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        # Parse header (optional)
        header = lines[0].split()
        if len(header) >= 2 and header[0].isdigit():
            rows = int(header[0])
            cols = int(header[1])
            start_idx = 1
        else:
            # Infer dimensions from content
            rows = len(lines)
            cols = max(len(line) for line in lines) if lines else 0
            start_idx = 0
        
        board = Board(rows, cols)
        bombs = set()
        
        # Parse board content
        board_lines = lines[start_idx:]
        for i, line in enumerate(board_lines):
            if i >= rows:
                break
            # Split line by spaces and filter out empty strings
            cells = [c for c in line.split() if c]
            # If no spaces, treat each character as a cell
            if not cells:
                cells = list(line)
            
            for j, char in enumerate(cells):
                if j >= cols:
                    break
                    
                if char in ['*', 'M', 'm']:
                    bombs.add((i, j))
                elif char.isdigit():
                    # Revealed cell with number
                    num = int(char)
                    board._board[i][j] = num
                    board._revealed_count += 1
        
        board._bombs = bombs
        return board

