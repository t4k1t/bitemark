"""Shared pytest fixtures for tests."""

import pytest


@pytest.fixture
def recipe_text_factory():
    """Build recipe markdown text with optional metadata and sections."""

    def _build_recipe_text(
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

    return _build_recipe_text
