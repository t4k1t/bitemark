"""BiteMark data models."""

from dataclasses import dataclass


@dataclass
class Ingredient:
    """Struct describing an ingredient."""

    name: str
    quantity: float
    unit: str
    quantity_max: float | None = None


@dataclass
class Instruction:
    """Struct describing an instruction step."""

    step: int
    description: str
