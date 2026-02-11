import requests
from bs4 import BeautifulSoup
import sys
import re
import time


def fetch_links(url, filter_pattern, limit=50):
    print(f"Fetching {url}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    links = set()

    # Get all links
    for a in soup.find_all("a", href=True):
        href = a["href"]

        # Resolve relative
        if href.startswith("/"):
            # Just rough base domain handling
            parts = url.split("/")
            base = f"{parts[0]}//{parts[2]}"
            href = base + href

        # Special handling for Pinch of Yum
        if "pinchofyum.com" in url:
            # We want https://pinchofyum.com/slug
            # We do NOT want https://pinchofyum.com/recipes/slug (categories)
            if "pinchofyum.com" in href:
                if "/recipes/" in href:
                    continue
                if "/about" in href or "/contact" in href or "/start-here" in href:
                    continue
                # Must have a slug (heuristic: length > 30 or dashes)
                if len(href.split("/")[-1]) > 5 or "-" in href.split("/")[-1]:
                    links.add(href)
            continue

        # Filter for others
        if filter_pattern and filter_pattern not in href:
            continue

        # Heuristics for "actual recipe page"
        # Most have /recipe/ or /recipes/ in the path, and likely end with a slug
        if "/recipe/" in href or "/recipes/" in href:
            # Avoid listicle pages if possible (often contain /gallery/ or /collection/)
            if "/gallery/" in href or "/collection/" in href or "/category/" in href:
                continue
            links.add(href)

    print(f"Found {len(links)} matching links on {url}")
    return list(links)[:limit]


def append_to_file(filename, links):
    if not links:
        return
    with open(filename, "a") as f:
        for link in links:
            f.write(link + "\n")
    print(f"Appended {len(links)} links to {filename}")


if __name__ == "__main__":
    sources = [
        # Allrecipes (very standard structure)
        {
            "url": "https://www.allrecipes.com/recipes/17562/dinner/",
            "filter": "allrecipes.com/recipe/",
        },
        # Pinch of Yum (Home page has latest recipes)
        {"url": "https://pinchofyum.com/", "filter": "pinchofyum.com/"},
        # Damn Delicious (Home)
        {"url": "https://damndelicious.net/", "filter": "damndelicious.net/"},
        # Two Peas and Their Pod
        {
            "url": "https://www.twopeasandtheirpod.com/",
            "filter": "twopeasandtheirpod.com/",
        },
    ]

    for source in sources:
        links = fetch_links(source["url"], source["filter"])
        append_to_file("data/test-recipes.txt", links)
        time.sleep(1)  # Be nice
