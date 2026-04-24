"""BiteMark data models."""

from dataclasses import dataclass


@dataclass
class Ingredient:
    """Struct describing an ingredient."""

    name: str
    # TODO: Handle fractions (e.g. 3/4 cup)
    quantity: float
    unit: str


@dataclass
class Instruction:
    """Struct describing an instruction step."""

    step: int
    description: str
