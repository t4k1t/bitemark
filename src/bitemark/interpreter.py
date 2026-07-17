"""Recipe interpretation and rendering logic."""

import logging

from bitemark.conversion import UnitConverter
from bitemark.domain import Ingredient, Instruction, Recipe
from bitemark.parsing import parse_recipe_text
from bitemark.rendering import render_recipe

logger = logging.getLogger(__name__)


class RecipeInterpreter:
    """Basic recipe interpreter."""

    FALLBACK_SERVINGS = 2.0

    def __init__(self, recipe_text: str):
        """Initialize RecipeInterpreter with recipe text."""
        self.recipe_text = recipe_text
        self.recipe: Recipe = parse_recipe_text(recipe_text)
        self.unit_converter = UnitConverter()

    @property
    def title(self) -> str | None:
        """Recipe title."""
        return self.recipe.title

    @property
    def metadata(self) -> dict[str, str]:
        """Recipe metadata."""
        return self.recipe.metadata

    @property
    def ingredients(self) -> list[Ingredient]:
        """Recipe ingredients."""
        return self.recipe.ingredients

    @ingredients.setter
    def ingredients(self, value: list[Ingredient]) -> None:
        self.recipe.ingredients = value

    @property
    def instructions(self) -> list[Instruction]:
        """Recipe instructions."""
        return self.recipe.instructions

    def convert_units(self, ingredient_name: str, target_unit: str):
        """Convert between ingredient units."""
        ingredient = next(
            (ing for ing in self.ingredients if ing.name.lower() == ingredient_name.lower()),
            None,
        )
        if not ingredient:
            return None

        converted = self.unit_converter.convert_ingredient(ingredient, target_unit)
        if converted is None:
            return None

        return {
            "name": converted.name,
            "quantity": converted.quantity.minimum,
            "unit": converted.unit,
            "quantity_max": converted.quantity.maximum,
        }

    def get_preferred_unit(self, ingredient: Ingredient, system: str | None = None):
        """Get preferred unit based on metadata. Falls back to 'metric' units."""
        unit_system = (system or self.metadata.get("units", "metric")).lower()
        return self.unit_converter.preferred_unit_for(ingredient, unit_system)

    def display_recipe(self, target_unit: str | None = None):
        """Print parsed recipe to standard output."""
        display_ingredients: list[Ingredient] = []
        for ingredient in self.ingredients:
            unit = self.get_preferred_unit(ingredient, target_unit)
            display_ingredient = ingredient
            if unit:
                converted = self.convert_units(ingredient.name, unit)
                if converted:
                    display_ingredient = Ingredient(
                        name=converted["name"],
                        quantity=converted["quantity"],
                        unit=converted["unit"],
                        quantity_max=converted["quantity_max"],
                    )
            display_ingredients.append(display_ingredient)

        print(render_recipe(self.recipe, ingredients=display_ingredients))

    def scale_ingredients(self, target_servings: str):
        """Scale ingredients based on number of servings."""
        try:
            target = float(target_servings)
        except (TypeError, ValueError) as exc:
            msg = "target_servings must be a positive number"
            raise ValueError(msg) from exc

        if target <= 0:
            msg = "target_servings must be a positive number"
            raise ValueError(msg)

        current_servings_raw = self.metadata.get("servings")
        try:
            if current_servings_raw is None:
                raise ValueError
            current_servings = float(current_servings_raw)
            if current_servings <= 0:
                raise ValueError
        except (TypeError, ValueError):
            logger.warning(
                "Invalid or missing recipe servings metadata (%r); falling back to 2 servings.",
                current_servings_raw,
            )
            current_servings = self.FALLBACK_SERVINGS

        scale_factor = target / current_servings

        self.ingredients = [self._scaled_ingredient(ingredient, scale_factor) for ingredient in self.ingredients]
        self.metadata["servings"] = str(target_servings)

    def _scaled_ingredient(self, ingredient: Ingredient, factor: float) -> Ingredient:
        quantity = ingredient.quantity_range().scaled(factor)
        return Ingredient(
            name=ingredient.name,
            quantity=quantity.minimum,
            unit=ingredient.unit,
            quantity_max=quantity.maximum,
        )
