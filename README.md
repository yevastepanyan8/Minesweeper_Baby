# Minesweeper Solver - AI Course Project

A modular Minesweeper solver implementation using CSP (Constraint Satisfaction Problem), probability inference, and BFS expansion strategies.

## Project Structure

```
Minesweeper_Baby/
├── solver/
│   ├── __init__.py          # Package initialization
│   ├── board.py             # Board representation and game state (Person 1)
│   ├── csp.py               # CSP inference engine (Person 1)
│   ├── strategy.py          # Main solver loop integration (Person 1)
│   ├── probability.py       # Probability-based selection (Person 2) ✨
│   ├── bfs.py               # BFS flood-fill for zero regions (Person 3) ✨
│   └── utils.py             # Utility functions
├── tests/
│   ├── test_board_simple.py # Board class tests
│   ├── test_csp_simple.py   # CSP engine tests
│   ├── test_probability_simple.py  # Probability module tests ✨
│   ├── test_bfs_simple.py          # BFS module tests ✨
│   └── example_boards/
│       ├── small_5x5.txt    # Small test board
│       └── medium_9x9.txt   # Medium test board
├── main.py                  # Main entry point
└── README.md                # This file
```

## Person 1 Deliverables (Completed)

### ✅ Board Representation (`board.py`)
- `Board` class with internal state management
- Tile states: UNKNOWN, SAFE, FLAGGED, REVEALED (0-8)
- Methods: `reveal()`, `flag()`, `neighbors()`, `count_adjacent_mines()`
- Board loading from text files
- ASCII visualization functions

### ✅ CSP Engine (`csp.py`)
- Constraint extraction from revealed tiles
- Simple constraint propagation (deterministic only)
- Inference rules for safe cells and mines
- Returns `(safe_cells, mine_cells)` lists

### ✅ Strategy Integration (`strategy.py`)
- Priority: CSP inference → Probability fallback
- Action application with BFS hooks

## Person 2 Deliverables (Completed) ✨

### ✅ Probability Engine (`probability.py`)

**Core Algorithm:**
1. **Local Constraint Analysis**: For each revealed tile, compute probabilities for unknown neighbors
2. **Constraint Combination**: Weighted average when multiple constraints affect the same cell
3. **Global Fallback**: Use global mine density when no local constraints exist
4. **Cell Selection**: Choose cell with lowest mine probability

**Rules Implemented:**
- **Rule A**: If `flagged_count == tile_value`, all remaining neighbors are safe (prob = 0)
- **Rule B**: If `remaining_mines == unknown_neighbors`, all are mines (prob = 1)
- **Rule C**: Local probability = `remaining_mines / unknown_neighbors`
- **Rule D**: Global fallback = `estimated_mines_left / unknown_cells`

**Key Functions:**
- `choose_cell(board)` - Main entry point, returns safest cell
- `compute_all_probabilities(board)` - Compute probabilities for all unknown cells
- `debug_probabilities(board)` - Return probability map for debugging
- `print_probability_map(board)` - Visual probability display

**Design Choices:**
- Uses weighted average to combine overlapping constraints
- Prefers local constraints over global estimates
- Tie-breaking: selects cell closest to board center
- No heavy SAT/backtracking - efficient approximations only

## Person 3 Deliverables (Completed) ✨

### ✅ BFS Flood-Fill Engine (`bfs.py`)

**Core Algorithm:**
1. **BFS Implementation**: Iterative breadth-first search using a queue
2. **Zero Expansion**: Reveals all connected zero tiles automatically
3. **Frontier Revelation**: Reveals numbered neighbors (frontier) but stops BFS there
4. **Edge Case Handling**: Respects flags, boundaries, and already-revealed tiles

**Why BFS over DFS:**
- **Bounded Memory**: Queue size bounded by frontier width (not depth)
- **Efficiency**: Better for wide zero regions common in Minesweeper
- **No Recursion Limits**: Iterative implementation avoids stack overflow
- **Predictable**: Level-by-level processing is easier to reason about

**How It Works:**
1. When a zero tile is revealed, `bfs_reveal()` is called
2. Starting from the zero tile, BFS processes all neighbors
3. If neighbor is zero → add to queue for further expansion
4. If neighbor is non-zero → reveal it (frontier) but don't continue BFS
5. Process continues until queue is empty

**Key Functions:**
- `bfs_reveal(board, start_i, start_j)` - Main BFS function, returns list of revealed cells
- `bfs_reveal_tuple(board, start)` - Convenience wrapper for tuple input

**Integration:**
- Automatically called from `strategy.py` after any zero tile reveal
- Works seamlessly with CSP (reveals more tiles for CSP to analyze)
- Works seamlessly with probability (more revealed tiles = better constraints)
- Does not interfere with solver loop iteration

**Design Choices:**
- Iterative BFS (no recursion) for reliability
- Returns list of revealed cells for state tracking
- Only uses public Board API (no internal access)
- Handles all edge cases: flags, boundaries, already-revealed tiles

## Usage

### Running the Solver

```bash
python main.py [board_file]
```

Example:
```bash
python main.py tests/example_boards/small_5x5.txt
```

### Running Tests

```bash
# Test board functionality
python tests/test_board_simple.py

# Test CSP engine
python tests/test_csp_simple.py

# Test probability module
python tests/test_probability_simple.py

# Test BFS module
python tests/test_bfs_simple.py
```

### Debugging Probabilities

```python
from solver.board import Board
from solver.probability import print_probability_map

board = Board.load_from_file("tests/example_boards/small_5x5.txt")
board.reveal(2, 2)  # Reveal a starting cell
print_probability_map(board)  # See probability map
```

## Board File Format

Text files represent boards with:
- First line (optional): `rows cols num_bombs`
- Following lines: Board representation
  - `.` or ` ` = empty/safe cell
  - `*` or `M` = mine
  - `0-8` = revealed cell with mine count

Example:
```
5 5 3
. . . . .
. * . . .
. . . . .
. . . * .
. . . . *
```

## Implementation Details

### Probability Engine Algorithm

1. **Extract Local Constraints**: For each revealed tile `(i,j)` with value `n`:
   - Count flagged neighbors: `f`
   - Count unknown neighbors: `u`
   - Remaining mines: `r = n - f`
   - Local probability: `p = r / u` (if `u > 0`)

2. **Combine Constraints**: When multiple constraints affect cell `(i,j)`:
   - Weighted average: `p_combined = (p1*c1 + p2*c2 + ...) / (c1 + c2 + ...)`
   - Where `c1, c2, ...` are constraint counts

3. **Global Fallback**: For cells with no local constraints:
   - Estimate: `p_global = mines_left / unknown_cells`
   - Uses heuristic mine density (~15% of board)

4. **Selection**: Choose cell with minimum probability, breaking ties by distance to center

### BFS Flood-Fill Algorithm

1. **Initialization**: Start from a zero tile `(i, j)`
2. **Queue Setup**: Add all unknown neighbors to BFS queue
3. **Processing Loop**:
   - Dequeue next tile
   - If unknown, reveal it
   - If revealed value is 0 → add its unknown neighbors to queue
   - If revealed value > 0 → stop BFS at this tile (frontier)
4. **Termination**: Stop when queue is empty

**Edge Cases Handled:**
- Flagged tiles: Never revealed, even if in zero region
- Out-of-bounds: Handled by `board.neighbors()` method
- Already-revealed: Skipped to avoid duplicate processing
- Non-zero tiles: Revealed as frontier but BFS stops

### Design Principles

- **Modular**: Each module has a clear responsibility
- **Extensible**: All three modules (CSP, Probability, BFS) work together seamlessly
- **Simple**: Efficient approximations, no heavy algorithms
- **Readable**: Well-documented code with clear function names
- **No GUI**: Terminal/ASCII output only

## Complete Solver Architecture

The solver integrates three complementary strategies:

1. **CSP (Person 1)**: Deterministic inference - finds guaranteed safe cells and mines
2. **Probability (Person 2)**: Probabilistic reasoning - estimates mine probabilities when CSP fails
3. **BFS (Person 3)**: Flood-fill expansion - automatically reveals connected zero regions

**Solver Flow:**
```
1. CSP inference → finds safe cells/mines
2. If no CSP results → Probability module → finds safest cell
3. Reveal chosen cell
4. If revealed cell is zero → BFS expands zero region
5. Repeat until solved or stuck
```

This three-module approach ensures:
- Maximum information extraction (CSP + BFS)
- Intelligent guessing when needed (Probability)
- Efficient exploration (BFS auto-reveal)

## Development Notes

- All code is original (not copied from reference projects)
- Reference projects were used only for architectural inspiration
- The solver is designed to be simple and educational
- No external dependencies required (pure Python)

## License

This project is for educational purposes as part of a university AI course.

