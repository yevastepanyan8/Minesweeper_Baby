"""Command-line helpers for running the Minesweeper solver."""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Dict, Iterable, List, Tuple

from minesweeper.core.board import Board
from minesweeper.core.strategy import DEFAULT_CONFIG, SolverConfig, solve_step, step
from minesweeper.utils.formatting import format_cells

STRATEGY_PRESETS: Dict[str, SolverConfig] = {
    "full": SolverConfig(),
    "full-nomc": SolverConfig(use_monte_carlo=False),
    "csp": SolverConfig(use_sat=False, use_probability=False, use_monte_carlo=False),
    "csp-sat": SolverConfig(use_probability=False, use_monte_carlo=False),
    "csp-prob": SolverConfig(use_sat=False, use_monte_carlo=False),
    "prob-only": SolverConfig(
        use_csp=False, use_sat=False, use_probability=True, use_monte_carlo=False
    ),
    "sat-only": SolverConfig(
        use_csp=False, use_probability=False, use_sat=True, use_monte_carlo=False
    ),
}

VALID_EXPANSIONS = {"bfs", "dfs"}
DIFFICULTY_PREFIXES = {
    "beginner": "beginner_",
    "intermediate": "intermediate_",
    "expert": "expert_",
}


def build_strategy_configs(specs: Iterable[str] | None) -> List[Tuple[str, SolverConfig]]:
    """Return a list of (name, config) pairs for the requested strategies."""
    if not specs:
        specs = ["full"]

    strategies: List[Tuple[str, SolverConfig]] = []
    for raw in specs:
        if ":" in raw:
            base, expansion = raw.split(":", 1)
        else:
            base, expansion = raw, None
        if base not in STRATEGY_PRESETS:
            raise ValueError(f"Unknown strategy '{base}'. Available: {', '.join(STRATEGY_PRESETS)}")
        config = replace(STRATEGY_PRESETS[base])
        label = base
        if expansion:
            expansion = expansion.lower()
            if expansion not in VALID_EXPANSIONS:
                raise ValueError(f"Invalid expansion '{expansion}'. Use bfs or dfs.")
            config = replace(config, expansion=expansion)
            label = f"{base}-{expansion}"
        strategies.append((label, config))
    return strategies


def _resolve_board_path(board_argument: str | None) -> str:
    """Return an absolute board path, defaulting to the bundled samples."""
    if board_argument:
        return board_argument

    project_root = Path(__file__).resolve().parent.parent
    default_board = project_root / "tests" / "data" / "boards" / "medium_9x9.txt"
    return str(default_board)


def run_solver(
    board: Board,
    source_label: str,
    strategy_config: SolverConfig = DEFAULT_CONFIG,
    verbose: bool = True,
) -> Dict[str, object]:
    """Execute the solver loop and return summary statistics."""
    max_iterations = 100
    iteration = 0
    start_time = perf_counter()

    if verbose:
        print("=" * 60)
        print("Minesweeper Solver - CLI")
        print("=" * 60)
        print(f"\nLoaded board: {source_label}\n")
        print("Initial Board State:")
        board.print_solver_view()
        print("Starting solver...\n")

    while not board.is_finished() and iteration < max_iterations:
        iteration += 1
        if verbose:
            print(f"\n--- Iteration {iteration} ---")

        if board.game_over:
            if verbose:
                _print_loss(board)
            break

        action, cells = step(board, config=strategy_config)

        if board.game_over:
            if verbose:
                _print_loss(board)
            break

        if action == "none" or not cells or action == "game_over":
            if verbose:
                if action == "game_over":
                    _print_loss(board)
                else:
                    print("No moves available. Solver stuck.")
            break

        if verbose:
            print(f"Action: {action}")
            print(f"Cells: {format_cells(cells)}")

        success = solve_step(board, action, cells, config=strategy_config)

        if board.game_over:
            if verbose:
                _print_loss(board)
            break

        if not success:
            if verbose:
                print("Warning: Action failed to apply.")
            break

        if verbose:
            board.print_solver_view()
            if board.is_finished():
                print("\n✓ Game finished! All safe cells revealed.")
                print("Game Over — WIN")

    if not board.game_over and iteration >= max_iterations and verbose:
        print(f"\nReached maximum iterations ({max_iterations}).")
        if board.is_finished():
            print("Game Over — WIN")
        else:
            print("Game Over — STUCK")

    runtime = perf_counter() - start_time
    stats = _gather_statistics(board, iteration)
    stats["runtime_sec"] = runtime
    stats["expanded_states"] = stats["revealed"]
    if verbose:
        _print_final_statistics(stats)
    return stats


def _print_loss(board: Board) -> None:
    """Display the losing state message."""
    print(f"\n✗ Hit a mine at {board.hit_mine_at}")
    print("Game Over — LOSS")


def _gather_statistics(board: Board, iterations: int) -> Dict[str, object]:
    unknown = board.unknown_cells()
    flagged = board.flagged_count()
    revealed = board.revealed_cells()

    if board.game_over:
        result = "loss"
    elif board.is_finished():
        result = "win"
    else:
        result = "stuck"

    return {
        "result": result,
        "hit_mine": board.hit_mine_at,
        "revealed": len(revealed),
        "flagged": flagged,
        "unknown": len(unknown),
        "iterations": iterations,
    }


def _print_final_statistics(stats: Dict[str, object]) -> None:
    """Display a summary of the run after the solver stops."""
    print("\n" + "=" * 60)
    print("Final Statistics:")
    print("=" * 60)

    if stats["result"] == "loss":
        print("Game Result: LOSS (mine hit)")
        print(f"Mine hit at: {stats['hit_mine']}")
    elif stats["result"] == "win":
        print("Game Result: WIN (all safe cells revealed)")
    else:
        print("Game Result: STUCK (no moves available)")

    print(f"Revealed cells: {stats['revealed']}")
    print(f"Flagged cells: {stats['flagged']}")
    print(f"Unknown cells: {stats['unknown']}")
    print(f"Iterations: {stats['iterations']}")
    print()


def _slugify_label(label: str | None) -> str:
    if not label:
        return "run"
    cleaned = []
    for char in label.lower():
        if char.isalnum():
            cleaned.append(char)
        elif char in {"-", "_"}:
            cleaned.append(char)
        else:
            cleaned.append("-")
    slug = "".join(cleaned).strip("-_")
    return slug or "run"


def _write_summary_csv(
    entries: List[Dict[str, object]],
    results_dir: str,
    label: str | None = None,
) -> str:
    results_path = Path(results_dir)
    results_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = _slugify_label(label)
    csv_path = results_path / "summary.csv"
    fieldnames = [
        "run_label",
        "run_timestamp",
        "board",
        "strategy",
        "result",
        "runtime_sec",
        "iterations",
        "expanded_states",
        "revealed",
        "flagged",
        "unknown",
        "hit_mine",
    ]
    write_header = not csv_path.exists() or csv_path.stat().st_size == 0
    with csv_path.open("a", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        for entry in entries:
            row = {key: entry.get(key, "") for key in fieldnames}
            row["run_label"] = slug
            row["run_timestamp"] = timestamp
            writer.writerow(row)
    return str(csv_path)


def _filter_by_difficulty(
    files: List[Path], difficulties: Iterable[str] | None,
) -> List[Path]:
    if not difficulties:
        return files
    prefixes = [DIFFICULTY_PREFIXES[d] for d in difficulties if d in DIFFICULTY_PREFIXES]
    if not prefixes:
        return files
    return [path for path in files if any(path.name.startswith(prefix) for prefix in prefixes)]


def run_batch(
    directory: str,
    strategies: List[Tuple[str, SolverConfig]],
    pattern: str = "*.txt",
    verbose: bool = False,
    results_dir: str = "results",
    difficulties: Iterable[str] | None = None,
) -> Dict[str, object]:
    """Solve every board matching pattern inside directory for each strategy."""
    board_dir = Path(directory)
    if not board_dir.exists():
        raise FileNotFoundError(f"Batch directory '{directory}' not found")

    files = sorted(board_dir.glob(pattern))
    files = _filter_by_difficulty(files, difficulties)
    strategy_totals = {
        name: {"total": 0, "solved": 0, "time": 0.0, "states": 0}
        for name, _ in strategies
    }
    entries: List[Dict[str, object]] = []

    for path in files:
        for strategy_name, config in strategies:
            board = Board.load_from_file(str(path))
            stats = run_solver(
                board,
                f"{path} [{strategy_name}]",
                strategy_config=config,
                verbose=verbose,
            )
            stats["board"] = str(path)
            stats["strategy"] = strategy_name
            entries.append(stats)

            totals = strategy_totals[strategy_name]
            totals["total"] += 1
            if stats["result"] == "win":
                totals["solved"] += 1
            totals["time"] += stats.get("runtime_sec", 0.0)
            totals["states"] += stats.get("expanded_states", 0)

            if not verbose:
                status = stats["result"].upper()
                print(
                    f"{path.name:30} [{strategy_name:10}] -> {status} "
                    f"({stats['iterations']} iters, {stats.get('runtime_sec', 0):.2f}s)"
                )

    strategy_names = [name for name, _ in strategies]
    strategy_label = strategy_names[0] if len(strategy_names) == 1 else f"{len(strategy_names)}-strategies"
    difficulty_label = (
        "-".join(sorted(difficulties)) if difficulties else "all"
    )
    label = f"{board_dir.name}_{strategy_label}_{difficulty_label}"

    csv_path = _write_summary_csv(entries, results_dir, label=label)

    return {
        "directory": str(board_dir),
        "pattern": pattern,
        "strategies": strategy_totals,
        "results": entries,
        "csv": csv_path,
    }


def print_batch_summary(summary: Dict[str, object]) -> None:
    print("\n" + "=" * 60)
    print(f"Batch results for {summary['directory']} ({summary['pattern']}):")
    print("=" * 60)
    for name, totals in summary["strategies"].items():
        total = totals["total"]
        solved = totals["solved"]
        rate = (solved / total * 100) if total else 0.0
        avg_time = (totals["time"] / total) if total else 0.0
        avg_states = (totals["states"] / total) if total else 0.0
        print(
            f"{name:15} -> {solved}/{total} wins | {rate:5.1f}% | "
            f"avg time {avg_time:.2f}s | avg states {avg_states:.1f}"
        )
    if summary.get("csv"):
        print(f"\nSummary CSV: {summary['csv']}")
    print()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Minesweeper solver")
    parser.add_argument(
        "board",
        nargs="?",
        help="Path to a board file (defaults to bundled medium board)",
    )
    parser.add_argument(
        "--random",
        nargs=3,
        metavar=("ROWS", "COLS", "MINES"),
        type=int,
        help="Generate a random board with lazy first-click placement",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Seed for random board generation (for reproducibility)",
    )
    parser.add_argument(
        "--batch",
        help="Directory containing board files to solve sequentially",
    )
    parser.add_argument(
        "--pattern",
        default="*.txt",
        help="Glob pattern for --batch runs (default: *.txt)",
    )
    parser.add_argument(
        "--strategy",
        action="append",
        help=(
            "Strategy preset (e.g. full, csp, csp-sat, prob-only). "
            "Append :dfs to switch expansion. Can be repeated."
        ),
    )
    parser.add_argument(
        "--results-dir",
        default="results",
        help="Directory to write batch summary CSV (default: results)",
    )
    parser.add_argument(
        "--difficulty",
        action="append",
        choices=sorted(DIFFICULTY_PREFIXES.keys()),
        help="Filter --batch runs to beginner/intermediate/expert board sets",
    )
    parser.add_argument(
        "--list-strategies",
        action="store_true",
        help="List available strategy presets and exit",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output for individual solves",
    )
    return parser


def _create_board_factory(parsed) -> Tuple[callable, str]:
    if parsed.random:
        rows, cols, mines = parsed.random
        label = f"random {rows}x{cols} with {mines} mines"

        def factory() -> Board:
            return Board(rows, cols, total_mines=mines, rng_seed=parsed.seed)

        return factory, label

    board_path = _resolve_board_path(parsed.board)
    path = Path(board_path)
    if path.exists():
        def loader() -> Board:
            return Board.load_from_file(board_path)

        return loader, board_path

    print(f"Error: Board file '{board_path}' not found.")
    print("Creating a simple test board instead...\n")
    fallback_bombs = {(0, 0), (1, 2), (4, 4)}

    def factory() -> Board:
        b = Board(5, 5, bombs=set(fallback_bombs))
        b.reveal(2, 2)
        return b

    return factory, "fallback 5x5 sample"


def main(argv: Iterable[str] | None = None) -> None:
    """Entry point used by `python -m` or the legacy main.py shim."""
    parser = _build_parser()
    parsed = parser.parse_args(sys.argv[1:] if argv is None else list(argv))

    if parsed.list_strategies:
        print("Available strategy presets:")
        for name in STRATEGY_PRESETS:
            print(f" - {name}")
        print("Append :dfs to any preset to use DFS expansion.")
        return

    try:
        strategies = build_strategy_configs(parsed.strategy)
    except ValueError as exc:
        parser.error(str(exc))

    if parsed.batch:
        if parsed.random:
            parser.error("--random cannot be combined with --batch")
        summary = run_batch(
            parsed.batch,
            strategies,
            pattern=parsed.pattern,
            verbose=not parsed.quiet,
            results_dir=parsed.results_dir,
            difficulties=parsed.difficulty,
        )
        print_batch_summary(summary)
        return

    board_factory, label = _create_board_factory(parsed)
    multiple = len(strategies) > 1

    for name, config in strategies:
        board = board_factory()
        current_label = f"{label} [{name}]" if multiple else label
        if multiple and not parsed.quiet:
            print("\n" + "#" * 20)
            print(f"Strategy: {name}")
            print("#" * 20)
        run_solver(board, current_label, strategy_config=config, verbose=not parsed.quiet)


if __name__ == "__main__":
    main()
