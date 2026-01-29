import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from formatters.recipe import RecipeFormatter


def load_urls():
    with open("test-recipes.txt", "r") as f:
        return [line.strip() for line in f if line.strip()]


@pytest.fixture(scope="module")
def formatter():
    return RecipeFormatter()


@pytest.mark.parametrize("url", load_urls())
def test_recipe_extraction(formatter, url):
    print(f"Testing {url}")
    result = formatter.parse_url(url)

    # Check for failures
    assert result.get("title"), f"Failed to extract title from {url}"
    assert result["title"] != "Error Parsing URL", (
        f"Parser returned error for {url}: {result.get('instructions')}"
    )

    # Ingredients check
    ingredients = result.get("ingredients", [])
    assert len(ingredients) > 0, f"No ingredients found for {url}"
    assert ingredients[0] != "(Could not auto-extract ingredients)", (
        f"Fallback ingredient msg found for {url}"
    )

    # Instructions check
    instructions = result.get("instructions", "")
    assert instructions, f"No instructions found for {url}"
    assert "Could not auto-extract" not in instructions, (
        f"Fallback matching failed for {url}"
    )
