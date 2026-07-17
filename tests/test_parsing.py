"""Tests for recipe parsing behavior."""

import pytest

from bitemark.main import RecipeInterpreter


class TestParsingBehavior:
    def test_parses_fraction_quantity(self, recipe_text_factory):
        interpreter = RecipeInterpreter(recipe_text_factory(ingredient_lines=["- 1/2 cup sugar"]))

        ingredient = interpreter.ingredients[0]
        assert ingredient.quantity == pytest.approx(0.5)
        assert ingredient.quantity_max is None
        assert ingredient.unit == "cup"
        assert ingredient.name == "sugar"

    def test_parses_mixed_number_quantity(self, recipe_text_factory):
        interpreter = RecipeInterpreter(recipe_text_factory(ingredient_lines=["- 1 1/2 tbsp oil"]))

        ingredient = interpreter.ingredients[0]
        assert ingredient.quantity == pytest.approx(1.5)
        assert ingredient.quantity_max is None
        assert ingredient.unit == "tbsp"
        assert ingredient.name == "oil"

    def test_parses_quantity_range(self, recipe_text_factory):
        interpreter = RecipeInterpreter(recipe_text_factory(ingredient_lines=["- 1-2 eggs"]))

        ingredient = interpreter.ingredients[0]
        assert ingredient.quantity == pytest.approx(1.0)
        assert ingredient.quantity_max == pytest.approx(2.0)
        assert ingredient.unit == ""
        assert ingredient.name == "eggs"

    def test_parses_decimal_quantity(self, recipe_text_factory):
        interpreter = RecipeInterpreter(recipe_text_factory(ingredient_lines=["- 1.25 cup milk"]))

        ingredient = interpreter.ingredients[0]
        assert ingredient.quantity == pytest.approx(1.25)
        assert ingredient.quantity_max is None

    def test_ignores_invalid_ingredient_line(self, recipe_text_factory):
        interpreter = RecipeInterpreter(recipe_text_factory(ingredient_lines=["- eggs", "- 2 eggs"]))

        assert len(interpreter.ingredients) == 1
        assert interpreter.ingredients[0].quantity == pytest.approx(2.0)

    def test_supports_directions_section_alias(self):
        recipe = (
            "# Soup\n\n"
            "## Ingredients\n\n"
            "- 1 liter water\n\n"
            "## Directions\n\n"
            "1. Boil.\n"
        )
        interpreter = RecipeInterpreter(recipe)

        assert len(interpreter.instructions) == 1
        assert interpreter.instructions[0].description == "Boil."

    def test_extracts_metadata_and_title(self, recipe_text_factory):
        interpreter = RecipeInterpreter(
            recipe_text_factory(
                metadata_lines=["servings: 4", "units: american", "cuisine: Italian"],
            ),
        )

        assert interpreter.title == "Pancakes"
        assert interpreter.metadata["servings"] == "4"
        assert interpreter.metadata["units"] == "american"
        assert interpreter.metadata["cuisine"] == "Italian"
