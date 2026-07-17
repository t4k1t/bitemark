"""Tests for rendering behavior."""

import pytest

from bitemark.main import RecipeInterpreter


def test_displays_quantity_range(
    recipe_text_factory,
    capsys: pytest.CaptureFixture[str],
):
    interpreter = RecipeInterpreter(
        recipe_text_factory(
            metadata_lines=["servings: 2"],
            ingredient_lines=["- 1-2 eggs"],
        ),
    )

    interpreter.scale_ingredients(4)
    interpreter.display_recipe()

    output = capsys.readouterr().out
    assert "- 2-4 eggs" in output
