"""DFS (Depth-First Search) flood fill for zero regions."""

from collections import deque
from typing import List, Tuple

from minesweeper.core.board import Board


def dfs_reveal(board: Board, start_i: int, start_j: int) -> List[Tuple[int, int]]:
    """Reveal connected zero tiles using a stack-based DFS."""
    revealed: List[Tuple[int, int]] = []

    if board.game_over:
        return revealed

    if not (0 <= start_i < board.rows and 0 <= start_j < board.cols):
        return revealed

    if board.is_flagged(start_i, start_j):
        return revealed

    start_value = board.get_tile(start_i, start_j)
    if start_value != 0:
        return revealed

    if not board.is_revealed(start_i, start_j) and board.reveal(start_i, start_j):
        revealed.append((start_i, start_j))

    stack = [(start_i, start_j)]
    visited = {(start_i, start_j)}

    while stack and not board.game_over:
        i, j = stack.pop()
        for ni, nj in board.neighbors(i, j):
            if (ni, nj) in visited or board.is_flagged(ni, nj):
                continue
            visited.add((ni, nj))
            if board.is_unknown(ni, nj) and board.reveal(ni, nj):
                revealed.append((ni, nj))
                value = board.get_tile(ni, nj)
                if value == 0:
                    stack.append((ni, nj))
    return revealed
