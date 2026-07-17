"""Tests for utility helpers."""

from pathlib import Path

from bitemark.util import extract_recipes_from_file


def test_extracts_single_recipe(tmp_path: Path):
    recipe_file = tmp_path / "recipes.md"
    recipe_file.write_text(
        "# One\n\n"
        "## Ingredients\n\n"
        "- 1 egg\n\n"
        "## Instructions\n\n"
        "1. Cook.\n",
        encoding="utf-8",
    )

    recipes = extract_recipes_from_file(recipe_file)

    assert len(recipes) == 1
    assert recipes[0].startswith("# One")


def test_extracts_multiple_recipes_by_same_level_headers(tmp_path: Path):
    recipe_file = tmp_path / "recipes.md"
    recipe_file.write_text(
        "# One\n\n"
        "## Ingredients\n\n"
        "- 1 egg\n\n"
        "## Instructions\n\n"
        "1. Cook.\n\n"
        "# Two\n\n"
        "## Ingredients\n\n"
        "- 2 eggs\n\n"
        "## Instructions\n\n"
        "1. Bake.\n",
        encoding="utf-8",
    )

    recipes = extract_recipes_from_file(recipe_file)

    assert len(recipes) == 2
    assert recipes[0].startswith("# One")
    assert recipes[1].startswith("# Two")


def test_extracts_multiple_recipes_when_new_header_level_is_higher_priority(tmp_path: Path):
    recipe_file = tmp_path / "recipes.md"
    recipe_file.write_text(
        "## One\n\n"
        "### Ingredients\n\n"
        "- 1 egg\n\n"
        "### Instructions\n\n"
        "1. Cook.\n\n"
        "## Two\n\n"
        "### Ingredients\n\n"
        "- 2 eggs\n\n"
        "### Instructions\n\n"
        "1. Bake.\n",
        encoding="utf-8",
    )

    recipes = extract_recipes_from_file(recipe_file)

    assert len(recipes) == 2
    assert recipes[0].startswith("## One")
    assert recipes[1].startswith("## Two")
