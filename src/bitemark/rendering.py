"""Rendering utilities for BiteMark recipes."""

from bitemark.domain import Ingredient, QuantityRange, Recipe


def format_quantity_display(quantity: QuantityRange) -> str:
    """Format a quantity range for output display."""
    formatted_minimum = _format_number(quantity.minimum)
    if quantity.maximum is None:
        return formatted_minimum
    formatted_maximum = _format_number(quantity.maximum)
    return f"{formatted_minimum}-{formatted_maximum}"


def render_recipe(recipe: Recipe, ingredients: list[Ingredient] | None = None) -> str:
    """Render recipe data as display text."""
    display_ingredients = ingredients if ingredients is not None else recipe.ingredients
    lines = ["Ingredients:"]
    for ingredient in display_ingredients:
        quantity_text = format_quantity_display(
            QuantityRange(minimum=ingredient.quantity, maximum=ingredient.quantity_max),
        )
        if ingredient.unit:
            lines.append(f"- {quantity_text} {ingredient.unit} {ingredient.name}")
        else:
            lines.append(f"- {quantity_text} {ingredient.name}")

    lines.append("")
    lines.append("Instructions:")
    for instruction in recipe.instructions:
        lines.append(f"{instruction.step}. {instruction.description}")
    return "\n".join(lines)


def _format_number(value: float) -> str:
    rounded = round(value, 2)
    if rounded == int(rounded):
        return str(int(rounded))
    return f"{rounded:.2f}".rstrip("0").rstrip(".")
