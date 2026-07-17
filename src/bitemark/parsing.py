"""Recipe and ingredient parsing logic."""

import re
from dataclasses import dataclass
from fractions import Fraction

from bitemark.domain import Ingredient, Instruction, QuantityRange, Recipe

QUANTITY_PART_PATTERN = r"(?:\d+\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?)"
QUANTITY_PATTERN = rf"{QUANTITY_PART_PATTERN}(?:\s*-\s*{QUANTITY_PART_PATTERN})?"
INGREDIENT_PATTERN = re.compile(rf"^- (?P<quantity>{QUANTITY_PATTERN})(?: (?P<rest>.+))?$")

METADATA_PATTERN = re.compile(r"^<!--(.*?)-->", re.DOTALL | re.MULTILINE)
INSTRUCTION_PATTERN = re.compile(r"(\d+)\. (.+)")


@dataclass(frozen=True)
class ParsedIngredientLine:
    """Normalized ingredient line parts parsed from Markdown."""

    quantity: QuantityRange
    unit: str
    name: str


def parse_recipe_text(recipe_text: str) -> Recipe:
    """Parse recipe markdown into a structured Recipe model."""
    metadata = extract_metadata(recipe_text)
    title = None
    ingredients: list[Ingredient] = []
    instructions: list[Instruction] = []

    lines = strip_metadata(recipe_text).split("\n")
    section = None

    for line in lines:
        if is_title_line(line):
            title = parse_title(line)
            continue

        next_section = parse_section(line)
        if next_section is not None:
            section = next_section
            continue

        if section == "ingredients":
            parsed_ingredient = parse_ingredient_line(line)
            if parsed_ingredient is None:
                continue
            ingredients.append(
                Ingredient(
                    name=parsed_ingredient.name,
                    quantity=parsed_ingredient.quantity.minimum,
                    unit=parsed_ingredient.unit,
                    quantity_max=parsed_ingredient.quantity.maximum,
                ),
            )
        elif section == "instructions":
            parsed_instruction = parse_instruction_line(line)
            if parsed_instruction is not None:
                instructions.append(parsed_instruction)

    return Recipe(title=title, metadata=metadata, ingredients=ingredients, instructions=instructions)


def extract_metadata(recipe_text: str) -> dict[str, str]:
    """Extract metadata from HTML comment at the top of the recipe."""
    match = METADATA_PATTERN.search(recipe_text)
    if not match:
        return {}

    meta_text = match.group(1)
    meta = {}
    for line in meta_text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()
    return meta


def parse_ingredient_line(line: str) -> ParsedIngredientLine | None:
    """Parse one Markdown ingredient list line into structured parts."""
    match = INGREDIENT_PATTERN.match(line)
    if not match:
        return None

    quantity = parse_quantity_range(match.group("quantity"))
    if quantity is None:
        return None

    rest = (match.group("rest") or "").strip()
    if not rest:
        return None

    unit, name = parse_unit_and_name(rest)
    if not name:
        return None

    return ParsedIngredientLine(quantity=quantity, unit=unit, name=name)


def parse_instruction_line(line: str) -> Instruction | None:
    """Parse instruction text line into an Instruction model."""
    match = INSTRUCTION_PATTERN.match(line)
    if not match:
        return None

    return Instruction(step=int(match.group(1)), description=match.group(2))


def parse_quantity_range(quantity_text: str) -> QuantityRange | None:
    """Parse a scalar or range quantity string into a QuantityRange."""
    parts = [part.strip() for part in quantity_text.split("-", maxsplit=1)]
    if len(parts) == 1:
        parsed_quantity = parse_single_quantity(parts[0])
        if parsed_quantity is None:
            return None
        return QuantityRange(minimum=parsed_quantity)

    start = parse_single_quantity(parts[0])
    end = parse_single_quantity(parts[1])
    if start is None or end is None:
        return None
    return QuantityRange(minimum=start, maximum=end)


def parse_single_quantity(quantity_text: str) -> float | None:
    """Parse an individual quantity token including fractions and mixed numbers."""
    text = quantity_text.strip()
    if not text:
        return None

    try:
        if " " in text:
            whole, fraction = text.split(maxsplit=1)
            return float(whole) + float(Fraction(fraction))
        if "/" in text:
            return float(Fraction(text))
        return float(text)
    except (ValueError, ZeroDivisionError):
        return None


def parse_unit_and_name(ingredient_text: str) -> tuple[str, str]:
    """Split an ingredient description into a unit token and ingredient name."""
    parts = ingredient_text.split(maxsplit=1)
    if len(parts) == 1:
        return "", parts[0]
    return parts[0], parts[1]


def strip_metadata(text: str) -> str:
    """Strip metadata comment block from recipe text."""
    return re.sub(r"^<!--.*?-->\n?", "", text, flags=re.DOTALL | re.MULTILINE)


def is_title_line(line: str) -> bool:
    """Return True when line is a markdown title line."""
    return line.startswith("# ")


def parse_title(line: str) -> str:
    """Parse markdown title text."""
    return line.lstrip("#").strip()


def parse_section(line: str) -> str | None:
    """Determine parser section from markdown heading line."""
    if line.startswith("## Ingredients"):
        return "ingredients"
    if line.startswith(("## Instructions", "## Directions")):
        return "instructions"
    return None
