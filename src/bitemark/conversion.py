"""Unit conversion utilities for ingredients."""

from dataclasses import dataclass

from bitemark.domain import Ingredient, QuantityRange


@dataclass(frozen=True)
class ConvertedIngredient:
    """Converted ingredient data used for display and downstream processing."""

    name: str
    quantity: QuantityRange
    unit: str


# TODO: Verify units and densities
# TODO: Extend units, densities, liquids
class UnitConverter:
    """Converts ingredient quantities between supported mass and volume units."""

    VOLUME_UNITS = {
        "ml": 1,
        "liter": 1000,
        "l": 1000,
        "cup_us": 240,
        "cup_uk": 284,
        "cup": 240,
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

    def convert_ingredient(self, ingredient: Ingredient, target_unit: str) -> ConvertedIngredient | None:
        """Convert ingredient quantity to target unit when possible."""
        source_unit = ingredient.unit.lower()
        target_unit = target_unit.lower()
        name_key = ingredient.name.lower()
        is_liquid = self._is_liquid_ingredient(name_key)

        quantity = QuantityRange(minimum=ingredient.quantity, maximum=ingredient.quantity_max)
        converted_quantity = self._convert_range(quantity, source_unit, target_unit, name_key, is_liquid)
        if converted_quantity is None:
            return None

        return ConvertedIngredient(name=ingredient.name, quantity=converted_quantity, unit=target_unit)

    def preferred_unit_for(self, ingredient: Ingredient, unit_system: str) -> str:
        """Return preferred display unit for an ingredient and unit system."""
        name = ingredient.name.lower()
        is_liquid = self._is_liquid_ingredient(name)
        normalized = unit_system.lower()
        if normalized == "metric":
            return "ml" if is_liquid else "g"
        if normalized == "american":
            return "cup" if is_liquid else "oz"
        if normalized == "british":
            return "pint" if is_liquid else "oz"
        return ingredient.unit

    def _is_liquid_ingredient(self, ingredient_name: str) -> bool:
        return any(liquid in ingredient_name for liquid in self.LIQUID_KEYWORDS)

    def _convert_range(
        self,
        quantity: QuantityRange,
        source_unit: str,
        target_unit: str,
        ingredient_name: str,
        is_liquid: bool,
    ) -> QuantityRange | None:
        converted_minimum = self._convert_quantity(
            quantity=quantity.minimum,
            source_unit=source_unit,
            target_unit=target_unit,
            ingredient_name=ingredient_name,
            is_liquid=is_liquid,
        )
        if converted_minimum is None:
            return None

        converted_maximum = None
        if quantity.maximum is not None:
            converted_maximum = self._convert_quantity(
                quantity=quantity.maximum,
                source_unit=source_unit,
                target_unit=target_unit,
                ingredient_name=ingredient_name,
                is_liquid=is_liquid,
            )
            if converted_maximum is None:
                return None

        return QuantityRange(minimum=converted_minimum, maximum=converted_maximum)

    def _convert_quantity(
        self,
        quantity: float,
        source_unit: str,
        target_unit: str,
        ingredient_name: str,
        is_liquid: bool,
    ) -> float | None:
        is_volume = source_unit in self.VOLUME_UNITS
        is_mass = source_unit in self.MASS_UNITS
        target_is_volume = target_unit in self.VOLUME_UNITS
        target_is_mass = target_unit in self.MASS_UNITS

        if is_volume and target_is_volume:
            return self._convert_volume_to_volume(quantity, source_unit, target_unit)
        if is_mass and target_is_mass:
            return self._convert_mass_to_mass(quantity, source_unit, target_unit)
        if is_volume and target_is_mass:
            if is_liquid:
                return None
            return self._convert_volume_to_mass(quantity, source_unit, target_unit, ingredient_name)
        if is_mass and target_is_volume:
            if is_liquid:
                return None
            return self._convert_mass_to_volume(quantity, source_unit, target_unit, ingredient_name)
        return None

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
