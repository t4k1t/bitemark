import sys
import re


def extract_all_recipes_from_markdown(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    recipes = []
    current_recipe = []
    in_recipe = False
    recipe_header_level = None

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


class RecipeInterpreter:
    def __init__(self, recipe_text):
        self.recipe_text = recipe_text
        self.metadata = self.extract_metadata()
        self.ingredients = []
        self.instructions = []
        self.parse_recipe()

    def extract_metadata(self):
        # Look for HTML comment at the top of the recipe
        metadata_pattern = re.compile(r"^<!--(.*?)-->", re.DOTALL | re.MULTILINE)
        match = metadata_pattern.search(self.recipe_text)
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
        text = re.sub(
            r"^<!--.*?-->\n?", "", self.recipe_text, flags=re.DOTALL | re.MULTILINE
        )
        lines = text.split("\n")
        section = None
        for line in lines:
            if line.startswith("## Ingredients"):
                section = "ingredients"
            elif line.startswith("## Instructions"):
                section = "instructions"
            elif section == "ingredients":
                self.parse_ingredient(line)
            elif section == "instructions":
                self.parse_instruction(line)

    def parse_ingredient(self, line):
        # Extract quantity, unit, and name
        match = re.match(r"- (\d+(\.\d+)?) (\w+) (.+)", line)
        if match:
            quantity = float(match.group(1))
            unit = match.group(3)
            name = match.group(4)
            self.ingredients.append({"name": name, "quantity": quantity, "unit": unit})

    def parse_instruction(self, line):
        # Extract step number and description
        match = re.match(r"(\d+)\. (.+)", line)
        if match:
            step_number = int(match.group(1))
            description = match.group(2)
            self.instructions.append({"step": step_number, "description": description})

    def convert_units(self, ingredient_name, target_unit):
        # Define conversion factors (all to base units: ml for volume, g for mass)
        volume_units = {
            "ml": 1,
            "liter": 1000,
            "l": 1000,
            "cup": 240,
            "tablespoon": 15,
            "tbsp": 15,
            "teaspoon": 5,
            "tsp": 5,
        }
        mass_units = {
            "g": 1,
            "gram": 1,
            "kg": 1000,
            "kilogram": 1000,
            "oz": 28.3495,
            "ounce": 28.3495,
            "lb": 453.592,
            "pound": 453.592,
        }
        target_unit = target_unit.lower()
        # Find ingredient by name (case-insensitive)
        ingredient = next(
            (
                ing
                for ing in self.ingredients
                if ing["name"].lower() == ingredient_name.lower()
            ),
            None,
        )
        if not ingredient:
            return None

        unit = ingredient["unit"].lower()

        # Determine unit type
        if unit in volume_units and target_unit in volume_units:
            base_qty = ingredient["quantity"] * volume_units[unit]
            converted_qty = base_qty / volume_units[target_unit]
        elif unit in mass_units and target_unit in mass_units:
            base_qty = ingredient["quantity"] * mass_units[unit]
            converted_qty = base_qty / mass_units[target_unit]
        else:
            # Incompatible or unknown units
            return None

        return {
            "name": ingredient["name"],
            "quantity": converted_qty,
            "unit": target_unit,
        }

    def scale_ingredients(self, target_servings):
        # Implement scaling logic here
        pass

    def display_recipe(self, target_unit=None):
        print("Ingredients:")
        for ingredient in self.ingredients:
            display_ingredient = ingredient
            if target_unit:
                converted = self.convert_units(ingredient["name"], target_unit)
                if converted:
                    display_ingredient = converted
            qty = round(display_ingredient["quantity"], 2)
            unit = display_ingredient["unit"]
            # Simple pluralization
            # if qty != 1 and not unit.endswith("s"):
            #     unit += "s"
            print(f"- {qty} {unit} {display_ingredient['name']}")
        print("\nInstructions:")
        for instruction in self.instructions:
            print(f"{instruction['step']}. {instruction['description']}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <markdown_file>")
        return

    recipes = extract_all_recipes_from_markdown(sys.argv[1])
    if not recipes:
        print("No recipes found in the file.")
        return

    for idx, recipe_text in enumerate(recipes, 1):
        print(f"\nRecipe {idx}:")
        interpreter = RecipeInterpreter(recipe_text)
        interpreter.display_recipe(target_unit="ml")


if __name__ == "__main__":
    main()
