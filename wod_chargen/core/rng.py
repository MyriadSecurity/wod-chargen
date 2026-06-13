"""Seeded procedural RNG."""

from __future__ import annotations

import random


class SeededRng:
    def __init__(self, seed: int) -> None:
        self._rng = random.Random(seed)

    def uniform(self) -> float:
        return self._rng.random()

    def choice(self, items: list):
        return self._rng.choice(items)

    def weighted_choice(self, items: list, weights: list[float]):
        return self._rng.choices(items, weights=weights, k=1)[0]

    def shuffle(self, items: list) -> list:
        copy = list(items)
        self._rng.shuffle(copy)
        return copy
