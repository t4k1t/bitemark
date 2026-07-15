"""Tests for RecipeInterpreter behavior."""

import logging

import pytest

from bitemark.main import RecipeInterpreter


def _recipe_text(
    metadata_lines: list[str] | None = None,
    ingredient_lines: list[str] | None = None,
    instruction_lines: list[str] | None = None,
) -> str:
    metadata = ""
    if metadata_lines:
        metadata_content = "\n".join(metadata_lines)
        metadata = f"<!--\n{metadata_content}\n-->\n"

    ingredients = ingredient_lines or ["- 100 g flour", "- 50 g sugar"]
    instructions = instruction_lines or ["1. Mix ingredients."]
    ingredients_text = "\n".join(ingredients)
    instructions_text = "\n".join(instructions)

    return (
        f"{metadata}# Pancakes\n\n"
        "## Ingredients\n\n"
        f"{ingredients_text}\n\n"
        "## Instructions\n\n"
        f"{instructions_text}\n"
    )


class TestScaleIngredients:
    def test_scales_quantities_from_metadata_servings(self):
        interpreter = RecipeInterpreter(_recipe_text(["servings: 4"]))

        interpreter.scale_ingredients(8)

        assert interpreter.ingredients[0].quantity == pytest.approx(200.0)
        assert interpreter.ingredients[1].quantity == pytest.approx(100.0)
        assert interpreter.metadata["servings"] == "8"

    def test_falls_back_to_two_servings_and_logs_warning(self, caplog: pytest.LogCaptureFixture):
        interpreter = RecipeInterpreter(_recipe_text())

        with caplog.at_level(logging.WARNING):
            interpreter.scale_ingredients(4)

        assert interpreter.ingredients[0].quantity == pytest.approx(200.0)
        assert interpreter.ingredients[1].quantity == pytest.approx(100.0)
        assert "falling back to 2 servings" in caplog.text

    def test_raises_for_non_positive_target_servings(self):
        interpreter = RecipeInterpreter(_recipe_text(["servings: 4"]))

        with pytest.raises(ValueError, match="target_servings must be a positive number"):
            interpreter.scale_ingredients(0)


class TestQuantityParsingAndDisplay:
    def test_parses_fraction_quantity(self):
        interpreter = RecipeInterpreter(_recipe_text(ingredient_lines=["- 1/2 cup sugar"]))

        ingredient = interpreter.ingredients[0]
        assert ingredient.quantity == pytest.approx(0.5)
        assert ingredient.quantity_max is None
        assert ingredient.unit == "cup"
        assert ingredient.name == "sugar"

    def test_parses_mixed_number_quantity(self):
        interpreter = RecipeInterpreter(_recipe_text(ingredient_lines=["- 1 1/2 tbsp oil"]))

        ingredient = interpreter.ingredients[0]
        assert ingredient.quantity == pytest.approx(1.5)
        assert ingredient.quantity_max is None
        assert ingredient.unit == "tbsp"
        assert ingredient.name == "oil"

    def test_parses_quantity_range(self):
        interpreter = RecipeInterpreter(_recipe_text(ingredient_lines=["- 1-2 eggs"]))

        ingredient = interpreter.ingredients[0]
        assert ingredient.quantity == pytest.approx(1.0)
        assert ingredient.quantity_max == pytest.approx(2.0)
        assert ingredient.unit == ""
        assert ingredient.name == "eggs"

    def test_scales_quantity_range(self):
        interpreter = RecipeInterpreter(
            _recipe_text(
                metadata_lines=["servings: 2"],
                ingredient_lines=["- 1-2 eggs"],
            ),
        )

        interpreter.scale_ingredients(4)

        ingredient = interpreter.ingredients[0]
        assert ingredient.quantity == pytest.approx(2.0)
        assert ingredient.quantity_max == pytest.approx(4.0)

    def test_displays_quantity_range(self, capsys: pytest.CaptureFixture[str]):
        interpreter = RecipeInterpreter(
            _recipe_text(
                metadata_lines=["servings: 2"],
                ingredient_lines=["- 1-2 eggs"],
            ),
        )

        interpreter.scale_ingredients(4)
        interpreter.display_recipe()

        output = capsys.readouterr().out
        assert "- 2-4 eggs" in output
