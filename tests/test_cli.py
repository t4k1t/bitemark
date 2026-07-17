"""Tests for CLI argument parsing and command behavior."""

import sys
from pathlib import Path

import pytest

from bitemark.cli import cli, parse_cli_args


def test_parse_cli_args_with_unit_and_servings():
    options = parse_cli_args(["--unit", "metric", "--servings", "4", "recipes.md"])

    assert options.unit == "metric"
    assert options.servings == "4"
    assert str(options.markdown_file) == "recipes.md"


def test_parse_cli_args_rejects_unknown_flag():
    with pytest.raises(ValueError, match="Unknown flag --bogus"):
        parse_cli_args(["--bogus", "recipes.md"])


def test_parse_cli_args_rejects_missing_unit_value():
    with pytest.raises(ValueError, match="Missing unit after unit flag"):
        parse_cli_args(["--unit"])


def test_parse_cli_args_rejects_missing_servings_value():
    with pytest.raises(ValueError, match="Missing servings after servings flag"):
        parse_cli_args(["--servings"])


def test_parse_cli_args_rejects_missing_markdown_path():
    with pytest.raises(ValueError, match="Invalid arguments"):
        parse_cli_args([])


def test_cli_returns_error_when_no_recipes_found(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    markdown_file = tmp_path / "empty.md"
    markdown_file.write_text("not a recipe\n", encoding="utf-8")

    original_argv = sys.argv
    sys.argv = ["bitemark", str(markdown_file)]
    try:
        result = cli()
    finally:
        sys.argv = original_argv

    output = capsys.readouterr()
    assert result == 1
    assert "No recipes found in the file." in output.err


def test_cli_renders_recipe_with_title(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    markdown_file = tmp_path / "recipe.md"
    markdown_file.write_text(
        "# Pancakes\n\n"
        "## Ingredients\n\n"
        "- 100 g flour\n\n"
        "## Instructions\n\n"
        "1. Mix ingredients.\n",
        encoding="utf-8",
    )

    original_argv = sys.argv
    sys.argv = ["bitemark", str(markdown_file)]
    try:
        result = cli()
    finally:
        sys.argv = original_argv

    output = capsys.readouterr()
    assert result == 0
    assert 'Recipe 1 "Pancakes":' in output.out
    assert "- 100 g flour" in output.out
    assert "1. Mix ingredients." in output.out
