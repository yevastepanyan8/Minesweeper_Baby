"""SAT-style inference for deducing guaranteed safe or mined cells."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, List, Sequence, Set, Tuple

from minesweeper.core.board import Board

Constraint = Tuple[Set[Tuple[int, int]], int]

# Limit component size / enumeration effort for brute-force SAT search
_MAX_COMPONENT_SIZE = 18
_MAX_ENUMERATIONS = 200_000


def _extract_constraints(board: Board) -> List[Constraint]:
    """Collect sum constraints from every revealed numbered tile."""
    constraints: List[Constraint] = []
    for i, j in board.revealed_cells():
        tile_value = board.get_tile(i, j)
        if tile_value <= 0 or tile_value == 9:
            continue

        neighbors = board.neighbors(i, j)
        unknown = {(ni, nj) for ni, nj in neighbors if board.is_unknown(ni, nj)}
        if not unknown:
            continue

        flagged = sum(1 for ni, nj in neighbors if board.is_flagged(ni, nj))
        required = tile_value - flagged
        required = max(0, min(required, len(unknown)))
        constraints.append((unknown, required))
    return constraints


def _build_components(constraints: Sequence[Constraint]) -> List[Set[Tuple[int, int]]]:
    """Group unknown cells that participate in shared constraints."""
    adjacency: Dict[Tuple[int, int], Set[Tuple[int, int]]] = defaultdict(set)
    for unknowns, _ in constraints:
        cells = list(unknowns)
        for idx, cell in enumerate(cells):
            for neighbor in cells[idx + 1 :]:
                adjacency[cell].add(neighbor)
                adjacency[neighbor].add(cell)

    visited: Set[Tuple[int, int]] = set()
    components: List[Set[Tuple[int, int]]] = []

    for cell in adjacency:
        if cell in visited:
            continue
        block: Set[Tuple[int, int]] = set()
        queue = deque([cell])
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            block.add(current)
            for neighbor in adjacency[current]:
                if neighbor not in visited:
                    queue.append(neighbor)
        components.append(block)

    return components


def _solve_component(
    component: Sequence[Tuple[int, int]],
    constraints: Sequence[Constraint],
) -> Tuple[Set[Tuple[int, int]], Set[Tuple[int, int]]]:
    """Enumerate satisfying assignments for a component."""
    if not component or len(component) > _MAX_COMPONENT_SIZE:
        return set(), set()

    cells = list(component)
    component_set = set(component)

    # Filter constraints that involve at least one cell from this component
    relevant: List[Constraint] = []
    for unknowns, required in constraints:
        overlap = {cell for cell in unknowns if cell in component_set}
        if overlap:
            relevant.append((overlap, required))

    if not relevant:
        return set(), set()

    constraint_membership: Dict[Tuple[int, int], List[int]] = defaultdict(list)
    required: List[int] = []
    unassigned: List[int] = []
    for idx, (unknowns, need) in enumerate(relevant):
        required.append(max(0, min(need, len(unknowns))))
        unassigned.append(len(unknowns))
        for cell in unknowns:
            constraint_membership[cell].append(idx)

    # Order variables by how constrained they are (more constrained first)
    ordered_cells = sorted(
        cells,
        key=lambda cell: len(constraint_membership.get(cell, ())),
        reverse=True,
    )

    cell_values: List[Set[int]] = [set() for _ in ordered_cells]
    current: List[int] = [0] * len(ordered_cells)
    assignment_count = 0
    abort = False

    def dfs(index: int) -> None:
        nonlocal assignment_count, abort
        if abort:
            return
        if index == len(ordered_cells):
            assignment_count += 1
            for idx, value in enumerate(current):
                cell_values[idx].add(value)
            if (
                assignment_count >= _MAX_ENUMERATIONS
                or all(len(values) == 2 for values in cell_values)
            ):
                abort = True
            return

        cell = ordered_cells[index]
        participating = constraint_membership.get(cell, ())
        for value in (0, 1):
            feasible = True
            current[index] = value
            updated: List[int] = []
            for con_idx in participating:
                unassigned[con_idx] -= 1
                if value == 1:
                    required[con_idx] -= 1
                updated.append(con_idx)
                if required[con_idx] < 0 or required[con_idx] > unassigned[con_idx]:
                    feasible = False
                    break
            if feasible:
                dfs(index + 1)
            for con_idx in updated:
                if value == 1:
                    required[con_idx] += 1
                unassigned[con_idx] += 1
            if abort:
                return
        current[index] = 0

    dfs(0)

    if assignment_count == 0:
        return set(), set()

    guaranteed_mines: Set[Tuple[int, int]] = set()
    guaranteed_safe: Set[Tuple[int, int]] = set()

    for idx, cell in enumerate(ordered_cells):
        values = cell_values[idx]
        if values == {1}:
            guaranteed_mines.add(cell)
        elif values == {0}:
            guaranteed_safe.add(cell)

    return guaranteed_safe, guaranteed_mines


def infer(board: Board) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
    """Run SAT-based reasoning to deduce safe and mine cells."""
    constraints = _extract_constraints(board)
    if not constraints:
        return [], []

    components = _build_components(constraints)
    safe: Set[Tuple[int, int]] = set()
    mines: Set[Tuple[int, int]] = set()

    for component in components:
        comp_safe, comp_mines = _solve_component(component, constraints)
        safe.update(comp_safe)
        mines.update(comp_mines)

    return list(safe), list(mines)
