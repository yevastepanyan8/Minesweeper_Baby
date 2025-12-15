# Minesweeper Solver - AI Course Project

A modular Minesweeper solver implementation using CSP (Constraint Satisfaction Problem), probability inference, and BFS expansion strategies.

## Project Structure

```
Minesweeper_Baby/
├── assets/
│   └── images/
│       └── Girlblogging.jpg           # Fun concept art / reference
├── main.py                            # CLI shim
├── minesweeper/
│   ├── __init__.py                    # Top-level package exports
│   ├── cli.py                         # Full solver CLI
│   ├── core/
│   │   ├── __init__.py
│   │   ├── board.py                   # Board representation + game state (Person 1)
│   │   └── strategy.py                # Main solver loop integration (Person 1)
│   ├── inference/
│   │   ├── __init__.py
│   │   ├── csp.py                     # CSP inference engine (Person 1)
│   │   ├── probability.py             # Probability-based selection (Person 2) ✨
│   │   └── sat.py                     # SAT-style deterministic inference ✨
│   ├── expansion/
│   │   ├── __init__.py
│   │   └── bfs.py                     # BFS flood-fill for zero regions (Person 3) ✨
│   └── utils/
│       ├── __init__.py
│       └── formatting.py              # Misc helpers
├── tests/
│   ├── data/
│   │   └── boards/
│   │       ├── small_5x5.txt          # Small test board
│   │       └── medium_9x9.txt         # Medium test board
│   └── unit/
│       ├── test_bfs_simple.py         # BFS module tests ✨
│       ├── test_probability_simple.py # Probability module tests ✨
│       ├── test_sat_inference.py      # SAT inference coverage ✨
│       └── test_board_generation.py   # Random board guarantees tests ✨
├── scripts/
│   └── run_boards.py                  # Batch runner helper ✨
├── results/
│   └── summary.csv                    # Latest batch summary output
└── README.md
```

## Person 1 Deliverables (Completed)

### ✅ Board Representation (`minesweeper/core/board.py`)
- `Board` class with internal state management
- Tile states: UNKNOWN, SAFE, FLAGGED, REVEALED (0-8)
- Methods: `reveal()`, `flag()`, `neighbors()`, `count_adjacent_mines()`
- Board loading from text files
- ASCII visualization functions
- Deferred mine placement to mimic real Minesweeper (first click and its neighbors are guaranteed safe when total mine count is provided)
- Helpers for tracking flagged count / remaining mines so probability estimates can use exact totals

### ✅ CSP Engine (`minesweeper/inference/csp.py`)
- Constraint extraction from revealed tiles
- Simple constraint propagation (deterministic only)
- Inference rules for safe cells and mines
- Returns `(safe_cells, mine_cells)` lists

### ✅ Strategy Integration (`minesweeper/core/strategy.py`)
- Priority: CSP inference → Probability fallback
- Action application with BFS hooks

## Person 2 Deliverables (Completed) ✨

### ✅ Probability Engine (`minesweeper/inference/probability.py`)

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

### ✅ Monte Carlo Sampling (`minesweeper/inference/montecarlo.py`)

- Samples random assignments that satisfy all local constraints to estimate mine probabilities
- Automatically handles small frontier components (configurable size limit and sample count)
- Feeds probabilistic guidance into the solver before the heuristic probability fallback
- Can be toggled via CLI strategies (e.g., `full` vs `full-nomc`) for ablation studies

## Person 3 Deliverables (Completed) ✨

### ✅ BFS Flood-Fill Engine (`minesweeper/expansion/bfs.py`)

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

## Advanced Inference ✨

### ✅ SAT Search (`minesweeper/inference/sat.py`)

**Why add SAT reasoning?**
- CSP rules only detect trivial "all safe" / "all mines" cases; SAT-style enumeration inspects entire frontier components
- Guarantees correctness for small clusters (≤12 cells) by checking every assignment satisfying all equations
- Provides deterministic mine flags before falling back to probabilistic guesses

**How it works:**
1. Extract constraints from every revealed numbered tile (unknown neighbors + required mine count)
2. Build connected components of frontier cells that participate in shared constraints
3. For each small component, enumerate all binary assignments that satisfy every constraint (brute-force SAT)
4. Cells that are 1 in every solution are flagged as mines; cells that are 0 in every solution are marked safe

**Integration:**
- `strategy.step()` now invokes SAT reasoning between CSP and probability fallbacks
- Honors a component size cap to keep enumeration tractable
- Fully optional—large frontier regions still fall back to the probabilistic module

## Usage

### Running the Solver

```bash
python main.py [board_file]
```

Example:
```bash
python main.py tests/data/boards/small_5x5.txt
```

You can also use the package entry point directly:
```bash
python -m minesweeper.cli tests/data/boards/small_5x5.txt
```

For a true Minesweeper experience (lazy mine placement with a guaranteed zero opening), generate a random board:
```bash
python -m minesweeper.cli --random 9 9 10        # add --seed <n> for reproducible boards
```

### Batch Evaluation & Strategy Comparisons

Benchmark multiple strategies on a directory of boards (comma-separated flags allowed):
```bash
python -m minesweeper.cli --batch tests/data/boards \
    --strategy full \
    --strategy csp-sat:dfs \
    --results-dir results
```

Need only a slice of the library? Repeat `--difficulty beginner|intermediate|expert` to restrict the batch:

```bash
python -m minesweeper.cli --batch tests/data/boards \
    --strategy csp-sat \
    --difficulty beginner --difficulty intermediate
```

Use `--strategy preset[:dfs]` to toggle CSP/SAT/probability combinations and choose BFS vs DFS expansion, or pass `--list-strategies` to see the presets. The batch run prints per-board outcomes, aggregates win rates/time/states per strategy, and appends rows to `results/summary.csv` with columns:
- `run_label`, `run_timestamp`, `board`, `strategy`, `result`, `runtime_sec`, `iterations`, `expanded_states`, `revealed`, `flagged`, `unknown`, `hit_mine`

Prefer a standalone helper? The script mirrors the CLI behavior:
```bash
python scripts/run_boards.py tests/data/boards --strategy full --strategy csp
```

### Running Tests

```bash
python tests/unit/test_probability_simple.py
python tests/unit/test_bfs_simple.py
python tests/unit/test_sat_inference.py
python tests/unit/test_board_generation.py
```

### Debugging Probabilities

```python
from minesweeper.core.board import Board
from minesweeper.inference.probability import print_probability_map

board = Board.load_from_file("tests/data/boards/small_5x5.txt")
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
