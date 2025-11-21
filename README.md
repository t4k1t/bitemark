# BiteMark

[![PyPI - Version](https://img.shields.io/pypi/v/bitemark.svg)](https://pypi.org/project/bitemark)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/bitemark.svg)](https://pypi.org/project/bitemark)
[![codecov](https://codecov.io/gh/t4k1t/bitemark/graph/badge.svg?token=Y5D4KX42LL)](https://codecov.io/gh/t4k1t/bitemark)

Reference implementation for `BiteMark` - a markup language for recipes based on Markdown.

## Why

I was looking for a uniform way to store my collected recipes in digital form. Since I've already stored my notes in Markdown format for many years, it seemed like a reasonable choice for recipes too:
1. It's human readable - so are recipes!
2. It's structured - so are recipes!
3. It's easily extensible
4. It's straighforward to format text and lists

## Why not JSON-LD?

Many websites expose recipe metadata in JSON-LD format which is great for extracting the data, but while this is technically human-readable, it's not a great experience.

## Specification

### Recipe Structure

```markdown
# <Recipe title>

## Ingredients

- <quantity> <unit> <ingredient>
- <quantity> <unit> <ingredient>

## Instructions

1. Step 1
2. Step 2
```

E.g. a very simple recipe could look like this:
```markdown
# Spaghetti Carbonara

## Ingredients

- 200 g spaghetti
- 100 g pancetta

## Instructions

1. Boil pasta.
2. Fry pancetta.
```

### Units

In order to facilitate unit conversion, units are sorted into two categories:
1. Volume
2. Mass

- **Volume:**  
    * `ml`
    * `liter / l`
    * `cup_us` - American cup
    * `cup_uk` - UK cup
    * `cup` - Defaults to American cup
    * `tablespoon / tbsp`
    * `teaspoon / tsp`
    * `pint`
- **Mass:**  
    * `g / gram`
    * `kg / kilogram`
    * `oz / ounce`
    * `lb / pound`

Non-liquid units can be converted between volume and mass based on a density table.

### Multiple Recipes

- A Markdown file may contain multiple recipes, each beginning with a Markdown header (`#` or `##`).

### Metadata (Optional)

Metadata can be placed at the top of the recipe inside an HTML comment block. This is so the metadata won't be rendered. This little syntactic trick is necessary because, sadly, Markdown does not support comments directly.

Here is an example for common metadata:
  ```markdown
  <!--
  servings: 4
  cuisine: Italian
  units: metric
  -->
  ```

There are no formal restrictions on which keys can be used in metadata.
