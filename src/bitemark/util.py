"""BiteMark utility functions."""

import re
from pathlib import Path


def extract_recipes_from_file(filepath: Path) -> list[str]:
    """Extract one or more recipe blocks from filepath."""
    with Path.open(filepath, encoding="utf-8") as f:
        lines = f.readlines()

    recipes = []
    current_recipe = []
    in_recipe = False
    recipe_header_level = 0

    header_pattern = re.compile(r"^(#{1,5})\s+")
    for line in lines:
        match = header_pattern.match(line)
        if match:
            level = len(match.group(1))
            if not in_recipe:
                in_recipe = True
                recipe_header_level = level
                current_recipe = [line.rstrip("\n")]
                continue

            elif level <= recipe_header_level:
                if current_recipe:
                    recipes.append("\n".join(current_recipe))
                recipe_header_level = level
                current_recipe = [line.rstrip("\n")]
                continue

        if in_recipe:
            current_recipe.append(line.rstrip("\n"))
    if current_recipe:
        recipes.append("\n".join(current_recipe))
    return recipes
