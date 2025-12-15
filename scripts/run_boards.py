"""Convenience script to run the solver across an entire directory of boards."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure the project root is on sys.path so "minesweeper" imports work
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from minesweeper.cli import build_strategy_configs, print_batch_summary, run_batch


def main() -> None:
    parser = argparse.ArgumentParser(description="Solve every board in a directory")
    parser.add_argument("directory", help="Folder containing board files")
    parser.add_argument(
        "--pattern",
        default="*.txt",
        help="Glob pattern for boards (default: *.txt)",
    )
    parser.add_argument(
        "--strategy",
        action="append",
        help="Strategy preset (e.g. full, csp, csp-prob[:dfs])",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed solver output for each board",
    )
    parser.add_argument(
        "--results-dir",
        default="results",
        help="Directory to write the summary CSV",
    )
    parser.add_argument(
        "--difficulty",
        action="append",
        choices=["beginner", "intermediate", "expert"],
        help="Restrict to beginner/intermediate/expert board subsets",
    )
    args = parser.parse_args()

    strategies = build_strategy_configs(args.strategy)
    summary = run_batch(
        args.directory,
        strategies,
        pattern=args.pattern,
        verbose=args.verbose,
        results_dir=args.results_dir,
        difficulties=args.difficulty,
    )
    print_batch_summary(summary)


if __name__ == "__main__":
    main()
