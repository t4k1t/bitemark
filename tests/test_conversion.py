"""Tests for conversion behavior."""

import pytest

from bitemark.main import RecipeInterpreter


class TestConversionBehavior:
    def test_convert_units_supports_mass_to_mass(self, recipe_text_factory):
        interpreter = RecipeInterpreter(recipe_text_factory(ingredient_lines=["- 100 g flour"]))

        converted = interpreter.convert_units("flour", "kg")

        assert converted is not None
        assert converted["quantity"] == pytest.approx(0.1)
        assert converted["unit"] == "kg"

    def test_convert_units_supports_volume_to_volume(self, recipe_text_factory):
        interpreter = RecipeInterpreter(recipe_text_factory(ingredient_lines=["- 1 cup milk"]))

        converted = interpreter.convert_units("milk", "ml")

        assert converted is not None
        assert converted["quantity"] == pytest.approx(240.0)
        assert converted["unit"] == "ml"

    def test_convert_units_uses_density_for_non_liquid(self, recipe_text_factory):
        interpreter = RecipeInterpreter(recipe_text_factory(ingredient_lines=["- 1 cup flour"]))

        converted = interpreter.convert_units("flour", "g")

        assert converted is not None
        assert converted["quantity"] == pytest.approx(127.2)
        assert converted["unit"] == "g"

    def test_convert_units_rejects_cross_dimension_for_liquid(self, recipe_text_factory):
        interpreter = RecipeInterpreter(recipe_text_factory(ingredient_lines=["- 1 cup milk"]))

        converted = interpreter.convert_units("milk", "g")

        assert converted is None

    def test_convert_units_returns_none_for_missing_ingredient(self, recipe_text_factory):
        interpreter = RecipeInterpreter(recipe_text_factory())

        converted = interpreter.convert_units("not-there", "g")

        assert converted is None

    def test_get_preferred_unit_respects_metadata_units(self, recipe_text_factory):
        interpreter = RecipeInterpreter(
            recipe_text_factory(
                metadata_lines=["units: american"],
                ingredient_lines=["- 100 g flour", "- 1 cup milk"],
            ),
        )

        assert interpreter.get_preferred_unit(interpreter.ingredients[0]) == "oz"
        assert interpreter.get_preferred_unit(interpreter.ingredients[1]) == "cup"
