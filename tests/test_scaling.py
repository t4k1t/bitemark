"""Tests for scaling behavior."""

import logging

import pytest

from bitemark.main import RecipeInterpreter


class TestScaleIngredients:
    def test_scales_quantities_from_metadata_servings(self, recipe_text_factory):
        interpreter = RecipeInterpreter(recipe_text_factory(["servings: 4"]))

        interpreter.scale_ingredients(8)

        assert interpreter.ingredients[0].quantity == pytest.approx(200.0)
        assert interpreter.ingredients[1].quantity == pytest.approx(100.0)
        assert interpreter.metadata["servings"] == "8"

    def test_falls_back_to_two_servings_and_logs_warning(
        self,
        recipe_text_factory,
        caplog: pytest.LogCaptureFixture,
    ):
        interpreter = RecipeInterpreter(recipe_text_factory())

        with caplog.at_level(logging.WARNING):
            interpreter.scale_ingredients(4)

        assert interpreter.ingredients[0].quantity == pytest.approx(200.0)
        assert interpreter.ingredients[1].quantity == pytest.approx(100.0)
        assert "falling back to 2 servings" in caplog.text

    def test_raises_for_non_positive_target_servings(self, recipe_text_factory):
        interpreter = RecipeInterpreter(recipe_text_factory(["servings: 4"]))

        with pytest.raises(ValueError, match="target_servings must be a positive number"):
            interpreter.scale_ingredients(0)

    def test_raises_for_non_numeric_target_servings(self, recipe_text_factory):
        interpreter = RecipeInterpreter(recipe_text_factory(["servings: 4"]))

        with pytest.raises(ValueError, match="target_servings must be a positive number"):
            interpreter.scale_ingredients("two")

    def test_scales_quantity_range(self, recipe_text_factory):
        interpreter = RecipeInterpreter(
            recipe_text_factory(
                metadata_lines=["servings: 2"],
                ingredient_lines=["- 1-2 eggs"],
            ),
        )

        interpreter.scale_ingredients(4)

        ingredient = interpreter.ingredients[0]
        assert ingredient.quantity == pytest.approx(2.0)
        assert ingredient.quantity_max == pytest.approx(4.0)
