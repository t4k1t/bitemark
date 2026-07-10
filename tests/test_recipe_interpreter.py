"""Tests for RecipeInterpreter behavior."""

import logging

import pytest

from bitemark.main import RecipeInterpreter


def _recipe_text(metadata_lines: list[str] | None = None) -> str:
    metadata = ""
    if metadata_lines:
        metadata_content = "\n".join(metadata_lines)
        metadata = f"<!--\n{metadata_content}\n-->\n"

    return (
        f"{metadata}# Pancakes\n\n"
        "## Ingredients\n\n"
        "- 100 g flour\n"
        "- 50 g sugar\n\n"
        "## Instructions\n\n"
        "1. Mix ingredients.\n"
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
