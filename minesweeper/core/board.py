"""
Board representation and internal game state model.

This module provides the Board class which maintains the internal state
of a Minesweeper game, including tile states, mine locations, and game logic.
"""

import random
from enum import IntEnum
from typing import List, Tuple, Set, Optional, Dict


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
    
    def __init__(
        self,
        rows: int,
        cols: int,
        bombs: Optional[Set[Tuple[int, int]]] = None,
        total_mines: Optional[int] = None,
        ensure_first_click_zero: bool = True,
        rng_seed: Optional[int] = None,
    ):
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
        self._bombs = set(bombs) if bombs is not None else set()
        self._revealed_count = 0
        self._flagged_count = 0
        self.game_over = False
        self.hit_mine_at = None
        self._first_click_zero = ensure_first_click_zero
        self._rng = random.Random(rng_seed)
        self._first_reveal_done = False

        if bombs is None and total_mines is None:
            self._total_mines: Optional[int] = None
        elif total_mines is not None:
            self._total_mines = total_mines
        else:
            self._total_mines = len(self._bombs)

        self._deferred_generation = bombs is None and (self._total_mines or 0) > 0
        self._mines_initialized = not self._deferred_generation
        
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

        if not self._mines_initialized:
            self._initialize_mines(i, j)

        # Check if it's a bomb (for simulation)
        first_action = not self._first_reveal_done
        if first_action and self._first_click_zero and (i, j) in self._bombs:
            self._relocate_first_click_bombs(i, j)

        if (i, j) in self._bombs:
            # Mark as 9 to indicate it's a mine
            self._board[i][j] = 9  # Special value for bomb (not a valid mine count)
            self._revealed_count += 1
            # Set game over state - game ends immediately when mine is hit
            self.game_over = True
            self.hit_mine_at = (i, j)
            self._first_reveal_done = True
            return True
        
        # Count adjacent mines
        count = self.count_adjacent_mines(i, j)
        self._board[i][j] = count
        self._revealed_count += 1
        self._first_reveal_done = True
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

    def _initialize_mines(self, start_i: int, start_j: int) -> None:
        """Lazily place mines after the first click, keeping the safe zone mine-free."""
        if self._mines_initialized:
            return
        if self._total_mines is None:
            raise ValueError("total_mines must be provided for deferred generation")

        safe_zone = {(start_i, start_j)}
        if self._first_click_zero:
            safe_zone.update(self.neighbors(start_i, start_j))

        def available_cells(exclusions: Set[Tuple[int, int]]):
            return [
                (i, j)
                for i in range(self.rows)
                for j in range(self.cols)
                if (i, j) not in exclusions
            ]

        candidates = available_cells(safe_zone)
        if len(candidates) < self._total_mines:
            # Relax guarantee to only the clicked cell if board is too dense
            safe_zone = {(start_i, start_j)}
            candidates = available_cells(safe_zone)

        if len(candidates) < self._total_mines:
            raise ValueError(
                "Not enough cells to place mines while respecting the first-click guarantee"
            )

        self._bombs = set(self._rng.sample(candidates, self._total_mines))
        self._mines_initialized = True

    def _relocate_first_click_bombs(self, start_i: int, start_j: int) -> bool:
        """Move mines away from the first click (and neighbors when requested)."""
        safe_zone = {(start_i, start_j)}
        if self._first_click_zero:
            safe_zone.update(self.neighbors(start_i, start_j))

        bombs_in_zone = self._bombs & safe_zone
        if not bombs_in_zone:
            return True

        def available_cells(exclusions: Set[Tuple[int, int]]):
            return [
                (i, j)
                for i in range(self.rows)
                for j in range(self.cols)
                if (i, j) not in self._bombs and (i, j) not in exclusions
            ]

        candidates = available_cells(safe_zone)
        if len(candidates) < len(bombs_in_zone):
            # Fall back to protecting only the clicked cell
            safe_zone = {(start_i, start_j)}
            bombs_in_zone = self._bombs & safe_zone
            candidates = available_cells(safe_zone)

        if len(candidates) < len(bombs_in_zone):
            return False

        replacements = self._rng.sample(candidates, len(bombs_in_zone))
        self._bombs.difference_update(bombs_in_zone)
        self._bombs.update(replacements)
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
        # Revealed tiles are: numbers 0-8, or 9 (mine)
        # FLAGGED is -2, UNKNOWN is -1
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

    def flagged_count(self) -> int:
        """Return how many tiles are currently flagged."""
        return self._flagged_count

    def total_mines(self) -> Optional[int]:
        """Return the known total mine count if available."""
        return self._total_mines

    def remaining_mines(self) -> Optional[int]:
        """Estimate the number of mines left based on total minus flagged."""
        if self._total_mines is None:
            return None
        return max(0, self._total_mines - self._flagged_count)
    
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
                elif val == 9:
                    row.append("*")  # Mine
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
                elif val == 9:
                    print(" *", end="")  # Mine
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
        
        bombs: Set[Tuple[int, int]] = set()
        revealed_values: Dict[Tuple[int, int], int] = {}

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
                    revealed_values[(i, j)] = num

        board = Board(rows, cols, bombs=bombs, ensure_first_click_zero=True)
        for (i, j), value in revealed_values.items():
            board._board[i][j] = value
            board._revealed_count += 1
        return board
