"""Standard implementation of the BiteMark recipe interpreter."""

import re
import sys
from pathlib import Path

from bitemark.models import Ingredient, Instruction
from bitemark.util import extract_recipes_from_file

# TODO: Refactor for readability


class RecipeInterpreter:
    HEADER_PATTERN = re.compile(r"^(#{1,5})\s+")
    METADATA_PATTERN = re.compile(r"^<!--(.*?)-->", re.DOTALL | re.MULTILINE)
    VOLUME_UNITS = {
        "ml": 1,
        "liter": 1000,
        "l": 1000,
        "cup_us": 240,
        "cup_uk": 284,
        "cup": 240,  # Default to American cup
        "tablespoon": 15,
        "tbsp": 15,
        "teaspoon": 5,
        "tsp": 5,
        "pint": 568,
    }
    MASS_UNITS = {
        "g": 1,
        "gram": 1,
        "kg": 1000,
        "kilogram": 1000,
        "oz": 28.3495,
        "ounce": 28.3495,
        "lb": 453.592,
        "pound": 453.592,
    }
    DENSITIES = {
        "flour": 0.53,
        "sugar": 0.85,
        "butter": 0.96,
        "milk": 1.03,
        "water": 1.0,
        "oil": 0.92,
        "oats": 0.41,
    }

    def __init__(self, recipe_text: str):
        """Initialize RecipeInterpreter with recipe text."""
        self.title: str | None = None
        self.recipe_text = recipe_text
        self.metadata = self.extract_metadata()
        self.ingredients: list[Ingredient] = []
        self.instructions: list[Instruction] = []
        self.parse_recipe()

    def extract_metadata(self):
        """Extract metadata from HTML comment at the top of the recipe."""
        match = self.METADATA_PATTERN.search(self.recipe_text)
        if not match:
            return {}
        meta_text = match.group(1)
        meta = {}
        for line in meta_text.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                meta[key.strip()] = value.strip()
        return meta

    def parse_recipe(self):
        # Remove metadata comment before parsing
        text = re.sub(r"^<!--.*?-->\n?", "", self.recipe_text, flags=re.DOTALL | re.MULTILINE)
        lines = text.split("\n")
        section = None
        for line in lines:
            if line.startswith("# "):
                self.title = line.lstrip("#").strip()
            elif line.startswith("## Ingredients"):
                section = "ingredients"
            elif line.startswith("## Instructions") or line.startswith("## Directions"):
                section = "instructions"
            elif section == "ingredients":
                self.parse_ingredient(line)
            elif section == "instructions":
                self.parse_instruction(line)

    def parse_ingredient(self, line: str):
        # Extract quantity, unit, and name
        match = re.match(r"- (\d+(\.\d+)?) (\w+) (.+)", line)
        if match:
            quantity = float(match.group(1))
            unit = match.group(3)
            name = match.group(4)
            self.ingredients.append(Ingredient(name=name, quantity=quantity, unit=unit))

    def parse_instruction(self, line: str):
        # Extract step number and description
        match = re.match(r"(\d+)\. (.+)", line)
        if match:
            step_number = int(match.group(1))
            description = match.group(2)
            self.instructions.append(Instruction(step=step_number, description=description))

    def convert_units(self, ingredient_name: str, target_unit: str):
        # Define conversion factors (all to base units: ml for volume, g for mass)
        target_unit = target_unit.lower()
        ingredient = next(
            (ing for ing in self.ingredients if ing.name.lower() == ingredient_name.lower()),
            None,
        )
        if not ingredient:
            return None

        unit = ingredient.unit.lower()
        qty = ingredient.quantity
        name_key = ingredient.name.lower()

        liquids = ["water", "milk", "oil"]
        is_liquid = any(liq in name_key for liq in liquids)

        is_volume = unit in self.VOLUME_UNITS
        is_mass = unit in self.MASS_UNITS
        target_is_volume = target_unit in self.VOLUME_UNITS
        target_is_mass = target_unit in self.MASS_UNITS

        # Volume to volume or mass to mass
        if is_volume and target_is_volume:
            base_qty = qty * self.VOLUME_UNITS[unit]
            converted_qty = base_qty / self.VOLUME_UNITS[target_unit]
        elif is_mass and target_is_mass:
            base_qty = qty * self.MASS_UNITS[unit]
            converted_qty = base_qty / self.MASS_UNITS[target_unit]
        # Volume to mass (only for non-liquids)
        elif is_volume and target_is_mass:
            if is_liquid:
                return None  # Don't convert liquid volume to mass
            density = None
            for k in self.DENSITIES:
                if k in name_key:
                    density = self.DENSITIES[k]
                    break
            if not density:
                return None
            ml = qty * self.VOLUME_UNITS[unit]
            grams = ml * density
            converted_qty = grams / self.MASS_UNITS[target_unit]
        # Mass to volume (only for non-liquids)
        elif is_mass and target_is_volume:
            if is_liquid:
                return None  # Don't convert liquid mass to volume
            density = None
            for k in self.DENSITIES:
                if k in name_key:
                    density = self.DENSITIES[k]
                    break
            if not density:
                return None
            grams = qty * self.MASS_UNITS[unit]
            ml = grams / density
            converted_qty = ml / self.VOLUME_UNITS[target_unit]
        else:
            return None

        return {
            "name": ingredient.name,
            "quantity": converted_qty,
            "unit": target_unit,
        }

    # TODO: Fix naming between system and target_unit
    def get_preferred_unit(self, ingredient: str, system: str or None = None):
        # Use metadata to determine system
        system = system or self.metadata.get("units", "metric").lower()
        # Simple heuristic: treat water, milk, oil as liquids
        liquids = ["water", "milk", "oil"]
        name = ingredient.name.lower()
        is_liquid = any(liq in name for liq in liquids)
        if system == "metric":
            return "ml" if is_liquid else "g"
        elif system == "american":
            return "cup" if is_liquid else "oz"
        elif system == "british":
            return "pint" if is_liquid else "oz"
        return ingredient.unit

    def display_recipe(self, target_unit: str | None = None):
        print("Ingredients:")
        for ingredient in self.ingredients:
            # Determine preferred unit if not specified
            unit = self.get_preferred_unit(ingredient, target_unit)
            display_ingredient = ingredient
            if unit:
                converted = self.convert_units(ingredient.name, unit)
                if converted:
                    display_ingredient = Ingredient(
                        name=converted["name"],
                        quantity=converted["quantity"],
                        unit=converted["unit"],
                    )
            qty = round(display_ingredient.quantity, 2)
            unit = display_ingredient.unit
            print(f"- {qty} {unit} {display_ingredient.name}")
        print("\nInstructions:")
        for instruction in self.instructions:
            print(f"{instruction.step}. {instruction.description}")

    def scale_ingredients(self, target_servings):
        # Implement scaling logic here
        pass


def cli():
    unit = None
    argv = sys.argv[1:]
    if len(sys.argv) < 1:
        print("Usage: bitemark <markdown_file>")
        exit(1)

    if len(sys.argv) > 4:
        print("Error: Too many arguments provided")
        exit(1)

    index_unit_argv = None
    for index, value in enumerate(argv):
        if value == "-u":
            index_unit_argv = index

    if index_unit_argv:
        if index_unit_argv + 1 >= len(argv):
            print("Error: Missing unit after -u flag")
            exit(1)

        unit = argv.pop(index_unit_argv + 1)
        del argv[index_unit_argv]

    if len(argv) != 1:
        print("Error: Invalid arguments: ", sys.argv[1:])
        exit(1)

    recipes = extract_recipes_from_file(Path(argv[0]))
    if not recipes:
        print("No recipes found in the file.")
        exit(1)

    for idx, recipe_text in enumerate(recipes, 1):
        prefix = f"\nRecipe {idx}"
        interpreter = RecipeInterpreter(recipe_text)
        title = f' "{interpreter.title}"' if interpreter.title else ""
        print(f"{prefix}{title}:")
        # Use units from metadata if present
        interpreter.display_recipe(target_unit=unit)


if __name__ == "__main__":
    cli()
