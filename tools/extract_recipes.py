import json
import logging
from recipe_scrapers import scrape_me
from recipe_scrapers._exceptions import WebsiteNotImplementedError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("extraction_errors.log"), logging.StreamHandler()],
)


def extract_recipes(input_file="data/test-recipes.txt", output_file="data/recipes.json"):
    recipes_data = []

    try:
        with open(input_file, "r") as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logging.error(f"Input file {input_file} not found.")
        return

    logging.info(f"Found {len(urls)} URLs to process.")

    for url in urls:
        logging.info(f"Processing: {url}")
        try:
            scraper = scrape_me(url)

            recipe_info = {
                "url": url,
                "title": scraper.title(),
                "ingredients": scraper.ingredients(),
                "instructions": scraper.instructions(),
                "image": scraper.image(),
                "yields": scraper.yields(),
                "nutrients": scraper.nutrients(),
            }

            recipes_data.append(recipe_info)
            logging.info(f"Successfully extracted: {recipe_info['title']}")

        except WebsiteNotImplementedError:
            logging.warning(f"Website not implemented/supported for URL: {url}")
        except Exception as e:
            logging.error(f"Failed to process {url}: {str(e)}")

    with open(output_file, "w") as f:
        json.dump(recipes_data, f, indent=2)

    logging.info(
        f"Extraction complete. {len(recipes_data)} recipes saved to {output_file}."
    )


if __name__ == "__main__":
    extract_recipes()
