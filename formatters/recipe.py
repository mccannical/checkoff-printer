import json

import requests
from bs4 import BeautifulSoup


class RecipeFormatter:
    def parse_url(self, url):
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # 1. Try JSON-LD (Best for modern recipe sites)
            scripts = soup.find_all("script", type="application/ld+json")
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    recipe_data = self._find_recipe_data(data)
                    if recipe_data:
                        return self._parse_json_ld(recipe_data)
                except Exception:
                    continue

            # 2. Fallback: Naive meta tag extraction
            title = soup.find("meta", property="og:title")
            title = title["content"] if title else soup.title.string

            # Very basic fallback for ingredients - tough to get right without schema
            # We return what we can
            return {
                "title": title.strip(),
                "ingredients": ["(Could not auto-extract ingredients)"],
                "instructions": "(Could not auto-extract instructions. Please copy paste text instead.)",
            }

        except Exception as e:
            return {
                "title": "Error Parsing URL",
                "ingredients": [],
                "instructions": str(e),
            }

    def _find_recipe_data(self, data):
        if isinstance(data, dict):
            type_val = data.get("@type", "")
            # Handle if @type is list ["Recipe", "NewsArticle"] or string "Recipe"
            if isinstance(type_val, list):
                if any("Recipe" in t for t in type_val):
                    return data
            elif isinstance(type_val, str) and "Recipe" in type_val:
                return data

            # Recurse into @graph if present
            if "@graph" in data:
                return self._find_recipe_data(data["@graph"])

            # Recurse into values just in case
            for key, value in data.items():
                res = self._find_recipe_data(value)
                if res:
                    return res

        elif isinstance(data, list):
            for item in data:
                res = self._find_recipe_data(item)
                if res:
                    return res

        return None

    def _parse_json_ld(self, data):
        title = data.get("name", "Untitled Recipe")

        ingredients = data.get("recipeIngredient", [])
        if isinstance(ingredients, str):
            ingredients = [ingredients]

        instructions_raw = data.get("recipeInstructions", [])
        instructions = []
        if isinstance(instructions_raw, list):
            for step in instructions_raw:
                if isinstance(step, dict):
                    instructions.append(step.get("text", ""))
                elif isinstance(step, str):
                    instructions.append(step)
        elif isinstance(instructions_raw, str):
            instructions.append(instructions_raw)

        return {
            "title": title,
            "ingredients": ingredients,
            "instructions": "\n".join(instructions),
        }

    def parse_text(self, title, raw_text):
        """
        Simple text parser. assumes user pasted a block of text.
        We can't easily separate ingredients/instructions without heuristics.
        For now, we just treat the whole blob as instructions.
        """
        return {
            "title": title or "Quick Recipe",
            "ingredients": [],  # User might need to format manually
            "instructions": raw_text,
        }
