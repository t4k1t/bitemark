"""Domain models for BiteMark recipes."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class QuantityRange:
    """Represents a scalar quantity or a minimum-maximum quantity range."""

    minimum: float
    maximum: float | None = None

    def scaled(self, factor: float) -> "QuantityRange":
        """Return a range scaled by the provided factor."""
        return QuantityRange(
            minimum=self.minimum * factor,
            maximum=self.maximum * factor if self.maximum is not None else None,
        )


@dataclass
class Ingredient:
    """Struct describing an ingredient."""

    name: str
    quantity: float
    unit: str
    quantity_max: float | None = None

    def quantity_range(self) -> QuantityRange:
        """Return the ingredient quantity represented as a range."""
        return QuantityRange(minimum=self.quantity, maximum=self.quantity_max)


@dataclass
class Instruction:
    """Struct describing an instruction step."""

    step: int
    description: str


@dataclass
class Recipe:
    """Parsed recipe data model."""

    title: str | None
    metadata: dict[str, str] = field(default_factory=dict)
    ingredients: list[Ingredient] = field(default_factory=list)
    instructions: list[Instruction] = field(default_factory=list)
