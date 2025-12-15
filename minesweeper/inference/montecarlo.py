"""Monte Carlo sampling for Minesweeper frontier probabilities."""

from __future__ import annotations

import random
from collections import defaultdict
from typing import Dict, List, Sequence, Set, Tuple

from minesweeper.core.board import Board

Constraint = Tuple[Set[Tuple[int, int]], int]


def _extract_constraints(board: Board) -> List[Constraint]:
    constraints: List[Constraint] = []
    for i, j in board.revealed_cells():
        val = board.get_tile(i, j)
        if val <= 0 or val == 9:
            continue
        neighbors = board.neighbors(i, j)
        unknown = {(ni, nj) for ni, nj in neighbors if board.is_unknown(ni, nj)}
        if not unknown:
            continue
        flagged = sum(1 for ni, nj in neighbors if board.is_flagged(ni, nj))
        required = val - flagged
        required = max(0, min(required, len(unknown)))
        constraints.append((unknown, required))
    return constraints


def _build_components(constraints: Sequence[Constraint]) -> List[Set[Tuple[int, int]]]:
    adjacency: Dict[Tuple[int, int], Set[Tuple[int, int]]] = defaultdict(set)
    for unknowns, _ in constraints:
        cells = list(unknowns)
        for idx, cell in enumerate(cells):
            for other in cells[idx + 1 :]:
                adjacency[cell].add(other)
                adjacency[other].add(cell)

    components: List[Set[Tuple[int, int]]] = []
    visited: Set[Tuple[int, int]] = set()

    for cell in adjacency:
        if cell in visited:
            continue
        stack = [cell]
        block: Set[Tuple[int, int]] = set()
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            block.add(current)
            stack.extend(neighbor for neighbor in adjacency[current] if neighbor not in visited)
        components.append(block)
    return components


def _constraints_for_component(
    component: Sequence[Tuple[int, int]],
    constraints: Sequence[Constraint],
) -> List[Constraint]:
    relevant: List[Constraint] = []
    comp_set = set(component)
    for unknowns, required in constraints:
        overlap = unknowns & comp_set
        if overlap:
            relevant.append((overlap, required))
    return relevant


def _random_assignment(
    cells: Sequence[Tuple[int, int]],
    constraints: Sequence[Constraint],
    rng: random.Random,
) -> Dict[Tuple[int, int], int] | None:
    if not cells:
        return {}

    constraint_membership: Dict[Tuple[int, int], List[int]] = defaultdict(list)
    required = []
    unassigned = []
    for idx, (overlap, need) in enumerate(constraints):
        required.append(need)
        unassigned.append(len(overlap))
        for cell in overlap:
            constraint_membership[cell].append(idx)

    ordered_cells = sorted(
        cells,
        key=lambda cell: (-len(constraint_membership.get(cell, ())), rng.random()),
    )
    assignments: Dict[Tuple[int, int], int | None] = {cell: None for cell in ordered_cells}

    def assign(index: int) -> bool:
        if index == len(ordered_cells):
            return all(req == 0 for req in required)

        cell = ordered_cells[index]
        participating = constraint_membership.get(cell, [])
        choices = [0, 1]
        rng.shuffle(choices)
        for value in choices:
            feasible = True
            assignments[cell] = value
            updated = []
            for con_idx in participating:
                unassigned[con_idx] -= 1
                if value == 1:
                    required[con_idx] -= 1
                updated.append(con_idx)
                if required[con_idx] < 0 or required[con_idx] > unassigned[con_idx]:
                    feasible = False
                    break
            if feasible and assign(index + 1):
                return True
            # revert
            assignments[cell] = None
            for con_idx in updated:
                unassigned[con_idx] += 1
                if value == 1:
                    required[con_idx] += 1
        return False

    if assign(0):
        return {cell: int(value) for cell, value in assignments.items() if value is not None}
    return None


def _sample_component(
    component: Sequence[Tuple[int, int]],
    constraints: Sequence[Constraint],
    samples: int,
    rng: random.Random,
) -> Dict[Tuple[int, int], float]:
    if not component or not constraints:
        return {}

    counts = {cell: 0 for cell in component}
    attempts = 0
    successes = 0
    while successes < samples and attempts < samples * 5:
        assignment = _random_assignment(component, constraints, rng)
        attempts += 1
        if assignment is None:
            continue
        successes += 1
        for cell, value in assignment.items():
            counts[cell] += value
    if successes == 0:
        return {}
    return {cell: counts[cell] / successes for cell in component}


def compute_probabilities(
    board: Board,
    samples: int = 256,
    max_component: int = 18,
    seed: int | None = None,
) -> Dict[Tuple[int, int], float]:
    constraints = _extract_constraints(board)
    components = _build_components(constraints)
    rng = random.Random(seed)
    probabilities: Dict[Tuple[int, int], float] = {}
    for component in components:
        size = len(component)
        if size == 0:
            continue
        relevant = _constraints_for_component(component, constraints)
        if not relevant:
            continue
        component_samples = samples
        if size > max_component:
            scale = max_component / size
            component_samples = max(32, int(samples * scale))
        probs = _sample_component(list(component), relevant, component_samples, rng)
        probabilities.update(probs)
    return probabilities


def choose_cell(board: Board) -> Tuple[int, int] | None:
    probabilities = compute_probabilities(board)
    if not probabilities:
        return None
    min_prob = min(probabilities.values())
    candidates = [cell for cell, prob in probabilities.items() if abs(prob - min_prob) < 1e-6]
    return min(candidates) if candidates else None
