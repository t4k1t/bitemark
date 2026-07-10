"""Standard implementation of the BiteMark recipe interpreter."""

import logging
import re
import sys
from pathlib import Path

from bitemark.models import Ingredient, Instruction
from bitemark.util import extract_recipes_from_file


logger = logging.getLogger(__name__)

class RecipeInterpreter:
    HEADER_PATTERN = re.compile(r"^(#{1,5})\s+")
    METADATA_PATTERN = re.compile(r"^<!--(.*?)-->", re.DOTALL | re.MULTILINE)
    INGREDIENT_PATTERN = re.compile(r"- (\d+(\.\d+)?) (\w+) (.+)")
    INSTRUCTION_PATTERN = re.compile(r"(\d+)\. (.+)")
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
    LIQUID_KEYWORDS = ("water", "milk", "oil")
    FALLBACK_SERVINGS = 2.0

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
        lines = self._strip_metadata(self.recipe_text).split("\n")
        section = None

        for line in lines:
            if self._is_title_line(line):
                self.title = self._parse_title(line)
                continue

            next_section = self._parse_section(line)
            if next_section is not None:
                section = next_section
                continue

            if section == "ingredients":
                self.parse_ingredient(line)
            elif section == "instructions":
                self.parse_instruction(line)

    def parse_ingredient(self, line: str):
        match = self.INGREDIENT_PATTERN.match(line)
        if not match:
            return

        quantity = float(match.group(1))
        unit = match.group(3)
        name = match.group(4)
        self.ingredients.append(Ingredient(name=name, quantity=quantity, unit=unit))

    def parse_instruction(self, line: str):
        match = self.INSTRUCTION_PATTERN.match(line)
        if not match:
            return

        step_number = int(match.group(1))
        description = match.group(2)
        self.instructions.append(Instruction(step=step_number, description=description))

    def convert_units(self, ingredient_name: str, target_unit: str):
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

        is_liquid = self._is_liquid_ingredient(name_key)

        is_volume = unit in self.VOLUME_UNITS
        is_mass = unit in self.MASS_UNITS
        target_is_volume = target_unit in self.VOLUME_UNITS
        target_is_mass = target_unit in self.MASS_UNITS

        if is_volume and target_is_volume:
            converted_qty = self._convert_volume_to_volume(qty, unit, target_unit)
        elif is_mass and target_is_mass:
            converted_qty = self._convert_mass_to_mass(qty, unit, target_unit)
        elif is_volume and target_is_mass:
            if is_liquid:
                return None
            converted_qty = self._convert_volume_to_mass(qty, unit, target_unit, name_key)
        elif is_mass and target_is_volume:
            if is_liquid:
                return None
            converted_qty = self._convert_mass_to_volume(qty, unit, target_unit, name_key)
        else:
            return None

        if converted_qty is None:
            return None

        return {
            "name": ingredient.name,
            "quantity": converted_qty,
            "unit": target_unit,
        }

    def get_preferred_unit(self, ingredient: Ingredient, system: str | None = None):
        # Use metadata to determine system
        unit_system = (system or self.metadata.get("units", "metric")).lower()
        name = ingredient.name.lower()
        is_liquid = self._is_liquid_ingredient(name)
        if unit_system == "metric":
            return "ml" if is_liquid else "g"
        if unit_system == "american":
            return "cup" if is_liquid else "oz"
        if unit_system == "british":
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
        """Scale ingredients based on number of servings."""
        try:
            target = float(target_servings)
        except (TypeError, ValueError) as exc:
            raise ValueError("target_servings must be a positive number") from exc

        if target <= 0:
            raise ValueError("target_servings must be a positive number")

        current_servings_raw = self.metadata.get("servings")
        try:
            current_servings = float(current_servings_raw)
            if current_servings <= 0:
                raise ValueError
        except (TypeError, ValueError):
            logger.warning(
                "Invalid or missing recipe servings metadata (%r); falling back to 2 servings.",
                current_servings_raw,
            )
            current_servings = self.FALLBACK_SERVINGS

        scale_factor = target / current_servings

        self.ingredients = [
            Ingredient(
                name=ingredient.name,
                quantity=ingredient.quantity * scale_factor,
                unit=ingredient.unit,
            )
            for ingredient in self.ingredients
        ]
        self.metadata["servings"] = str(target_servings)

    def _strip_metadata(self, text: str) -> str:
        return re.sub(r"^<!--.*?-->\n?", "", text, flags=re.DOTALL | re.MULTILINE)

    def _is_title_line(self, line: str) -> bool:
        return line.startswith("# ")

    def _parse_title(self, line: str) -> str:
        return line.lstrip("#").strip()

    def _parse_section(self, line: str) -> str | None:
        if line.startswith("## Ingredients"):
            return "ingredients"
        if line.startswith("## Instructions") or line.startswith("## Directions"):
            return "instructions"
        return None

    def _is_liquid_ingredient(self, ingredient_name: str) -> bool:
        return any(liquid in ingredient_name for liquid in self.LIQUID_KEYWORDS)

    def _convert_volume_to_volume(self, quantity: float, source_unit: str, target_unit: str) -> float:
        base_qty = quantity * self.VOLUME_UNITS[source_unit]
        return base_qty / self.VOLUME_UNITS[target_unit]

    def _convert_mass_to_mass(self, quantity: float, source_unit: str, target_unit: str) -> float:
        base_qty = quantity * self.MASS_UNITS[source_unit]
        return base_qty / self.MASS_UNITS[target_unit]

    def _convert_volume_to_mass(
        self,
        quantity: float,
        source_unit: str,
        target_unit: str,
        ingredient_name: str,
    ) -> float | None:
        density = self._density_for_ingredient(ingredient_name)
        if density is None:
            return None

        ml = quantity * self.VOLUME_UNITS[source_unit]
        grams = ml * density
        return grams / self.MASS_UNITS[target_unit]

    def _convert_mass_to_volume(
        self,
        quantity: float,
        source_unit: str,
        target_unit: str,
        ingredient_name: str,
    ) -> float | None:
        density = self._density_for_ingredient(ingredient_name)
        if density is None:
            return None

        grams = quantity * self.MASS_UNITS[source_unit]
        ml = grams / density
        return ml / self.VOLUME_UNITS[target_unit]

    def _density_for_ingredient(self, ingredient_name: str) -> float | None:
        for name, density in self.DENSITIES.items():
            if name in ingredient_name:
                return density
        return None


def cli():
    unit = None
    servings = None
    usage = "Usage: bitemark [-u UNIT|--unit UNIT] [-s SERVINGS|--servings SERVINGS] <markdown_file>"
    raw_argv = sys.argv[1:]
    argv = []

    index = 0
    while index < len(raw_argv):
        value = raw_argv[index]
        if value in ("-u", "--unit"):
            if index + 1 >= len(raw_argv):
                print("Error: Missing unit after unit flag")
                print(usage)
                exit(1)
            unit = raw_argv[index + 1]
            index += 2
            continue

        if value in ("-s", "--servings"):
            if index + 1 >= len(raw_argv):
                print("Error: Missing servings after servings flag")
                print(usage)
                exit(1)
            servings = raw_argv[index + 1]
            index += 2
            continue

        if value.startswith("-"):
            print(f"Error: Unknown flag {value}")
            print(usage)
            exit(1)

        argv.append(value)
        index += 1

    if len(argv) != 1:
        print("Error: Invalid arguments: ", sys.argv[1:])
        print(usage)
        exit(1)

    recipes = extract_recipes_from_file(Path(argv[0]))
    if not recipes:
        print("No recipes found in the file.")
        exit(1)

    for idx, recipe_text in enumerate(recipes, 1):
        prefix = f"\nRecipe {idx}"
        interpreter = RecipeInterpreter(recipe_text)
        if servings is not None:
            try:
                interpreter.scale_ingredients(servings)
            except ValueError as exc:
                print(f"Error: {exc}")
                exit(1)
        title = f' "{interpreter.title}"' if interpreter.title else ""
        print(f"{prefix}{title}:")
        # Use units from metadata if present
        interpreter.display_recipe(target_unit=unit)


if __name__ == "__main__":
    cli()
