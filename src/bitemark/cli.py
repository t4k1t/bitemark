"""CLI for the BiteMark interpreter."""

import sys
from dataclasses import dataclass
from pathlib import Path

from bitemark.interpreter import RecipeInterpreter
from bitemark.util import extract_recipes_from_file


@dataclass(frozen=True)
class CliOptions:
    """Normalized CLI options parsed from argv."""

    unit: str | None
    servings: str | None
    markdown_file: Path


def cli() -> int:
    """Command line interface entry point."""
    usage = "Usage: bitemark [-u UNIT|--unit UNIT] [-s SERVINGS|--servings SERVINGS] <markdown_file>"
    try:
        options = parse_cli_args(sys.argv[1:])
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        print(usage, file=sys.stderr)
        return 1

    recipes = extract_recipes_from_file(options.markdown_file)
    if not recipes:
        print("No recipes found in the file.", file=sys.stderr)
        return 1

    for idx, recipe_text in enumerate(recipes, 1):
        prefix = f"\nRecipe {idx}"
        interpreter = RecipeInterpreter(recipe_text)
        if options.servings is not None:
            try:
                interpreter.scale_ingredients(options.servings)
            except ValueError as exc:
                print(f"Error: {exc}")
                return 1
        title = f' "{interpreter.title}"' if interpreter.title else ""
        print(f"{prefix}{title}:")
        interpreter.display_recipe(target_unit=options.unit)

    return 0


def parse_cli_args(argv: list[str]) -> CliOptions:
    """Parse CLI arguments into normalized options."""
    unit = None
    servings = None
    positional: list[str] = []

    index = 0
    while index < len(argv):
        value = argv[index]
        if value in ("-u", "--unit"):
            if index + 1 >= len(argv):
                msg = "Missing unit after unit flag"
                raise ValueError(msg)
            unit = argv[index + 1]
            index += 2
            continue

        if value in ("-s", "--servings"):
            if index + 1 >= len(argv):
                msg = "Missing servings after servings flag"
                raise ValueError(msg)
            servings = argv[index + 1]
            index += 2
            continue

        if value.startswith("-"):
            msg = f"Unknown flag {value}"
            raise ValueError(msg)

        positional.append(value)
        index += 1

    if len(positional) != 1:
        msg = f"Invalid arguments: {argv}"
        raise ValueError(msg)

    return CliOptions(unit=unit, servings=servings, markdown_file=Path(positional[0]))
