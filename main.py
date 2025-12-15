"""Compatibility shim for running the Minesweeper solver via `python main.py`."""

from minesweeper.cli import main

if __name__ == "__main__":
    main()
