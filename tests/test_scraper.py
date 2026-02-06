import pytest
from unittest.mock import Mock, patch
from backend.scraper import (
    scrape_recipe,
    _post_process_grouped_ingredients,
    _is_instagram_url,
    _extract_instagram_caption_from_html,
    _parse_instagram_caption,
    _instagram_candidate_urls,
    _scrape_instagram_recipe,
)

def test_scrape_recipe_success():
    """Test scraping a valid recipe URL"""
    # Using AllRecipes as a test case (well-supported site)
    url = "https://www.allrecipes.com/recipe/12151/banana-cream-pie-i/"

    recipe_data = scrape_recipe(url)

    assert recipe_data is not None
    assert recipe_data['title'] is not None
    assert len(recipe_data['title']) > 0
    assert recipe_data['ingredients'] is not None
    assert len(recipe_data['ingredients']) > 0
    assert recipe_data['instructions'] is not None

def test_scrape_recipe_invalid_url():
    """Test that invalid URLs raise appropriate error"""
    with pytest.raises(ValueError):
        scrape_recipe("not-a-valid-url")

def test_scrape_recipe_with_wild_mode():
    """Test scraping with wild_mode for unsupported sites"""
    # This will test a site that might not have explicit support
    url = "https://example-recipe-blog.com/recipe"

    # Should not raise error due to wild_mode
    result = scrape_recipe(url)
    assert result is not None or result.get('error') is not None


def test_post_process_grouped_ingredients_bun_rieu_cleanup():
    """Normalizes malformed section names and rebalances known Bun Rieu ingredient groups."""
    raw_groups = [
        {
            'section': 'Broth:',
            'items': ['8 quarts Water', '4 lbs Pork Ribs', '1 lb Ground Pork', '16 oz Jumbo Lump Crab Meat'],
        },
        {
            'section': 'Step 2',
            'items': ['1/2 cup Dried Shrimp', '1 Yellow Onion'],
        },
        {
            'section': 'Toppings:',
            'items': [
                'Cha chien (Fried Vietnamese Ham)',
                'Green Leaf Lettuce',
                'Banana Blossom (Optional)',
                'Beansprouts (Optional)',
                'Cilantro',
                'Green Onions',
                'Vietnamese Perilla',
                'Limes',
                'Thai Chili',
            ],
        },
        {
            'section': 'Noodles:',
            'items': ['7 oz Crab Paste With Soya Oil', '32 oz Vermicelli Noodles'],
        },
        {
            'section': 'Finish Broth:',
            'items': [
                '2 cubes Bun Rieu Seasoning',
                '3 tbsp Fish Sauce',
                '1 inch Nub of Rock Sugar',
                '3 tbsp MSG',
                '1 tbsp Mam Ruoc (fermented shrimp paste) (Optional)',
                '7 oz Crab Paste With Soya Oil',
                '1 tbsp Fish Sauce',
                'Fermented Shrimp Paste',
            ],
        },
        {
            'section': 'Rieu/Meatballs:',
            'items': ['3 Eggs'],
        },
        {
            'section': 'Add',
            'items': ['4 large Roma Tomatoes', 'Salt to Taste', 'Salt and Pepper to Taste', 'Tofu Puffs'],
        },
    ]

    processed = _post_process_grouped_ingredients(raw_groups)
    section_map = {group['section']: group['items'] for group in processed}

    assert 'Step 2' not in section_map
    assert 'Add' not in section_map
    assert 'Broth' in section_map
    assert 'Crab Meatball (Rieu)' in section_map
    assert 'Noodles' in section_map
    assert 'Toppings' in section_map
    assert 'Garnishes' in section_map
    assert '1 lb Ground Pork' in section_map['Crab Meatball (Rieu)']
    assert '16 oz Jumbo Lump Crab Meat' in section_map['Crab Meatball (Rieu)']
    assert '32 oz Vermicelli Noodles' in section_map['Noodles']
    assert 'Tofu Puffs' in section_map['Toppings']
    assert 'Fermented Shrimp Paste' in section_map['Garnishes']


def test_is_instagram_url():
    assert _is_instagram_url("https://www.instagram.com/p/ABC123/")
    assert _is_instagram_url("https://instagram.com/reel/XYZ456/")
    assert _is_instagram_url("https://www.instagram.com/reels/XYZ456/")
    assert _is_instagram_url("https://instagr.am/p/ABC123/")
    assert not _is_instagram_url("https://www.allrecipes.com/recipe/12151/banana-cream-pie-i/")
    assert not _is_instagram_url("https://www.instagram.com/some_profile/")


def test_extract_instagram_caption_from_html_og_description():
    html = """
    <html>
      <head>
        <meta property="og:description" content='chefaccount on Instagram: "Ingredients:\\n2 cups flour\\nInstructions:\\nMix and bake."' />
      </head>
    </html>
    """
    caption = _extract_instagram_caption_from_html(html)
    assert "Ingredients:" in caption
    assert "2 cups flour" in caption
    assert "Instructions:" in caption


def test_parse_instagram_caption_sections():
    caption = """
    Weeknight Garlic Chicken
    Ingredients:
    Chicken:
    1 lb chicken thighs
    1 tsp salt
    Sauce:
    2 tbsp yogurt
    Instructions:
    Sear the chicken.
    Mix the sauce and toss.
    Serve hot.
    """
    parsed = _parse_instagram_caption(caption)

    assert parsed["title"] == "Weeknight Garlic Chicken"
    assert parsed["ingredients"]
    sections = {group["section"]: group["items"] for group in parsed["ingredients"]}
    assert "Chicken" in sections
    assert "Sauce" in sections
    assert "1 lb chicken thighs" in sections["Chicken"]
    assert "2 tbsp yogurt" in sections["Sauce"]
    assert "Step 1" in parsed["instructions"]
    assert "Step 2" in parsed["instructions"]


def test_instagram_candidate_urls_include_embed():
    urls = _instagram_candidate_urls("https://www.instagram.com/reel/XYZ456/?igsh=abc")
    assert urls[0] == "https://www.instagram.com/reel/XYZ456/"
    assert "https://www.instagram.com/reel/XYZ456/?hl=en" in urls
    assert "https://www.instagram.com/reel/XYZ456/embed/captioned/" in urls
    assert "https://www.instagram.com/reel/XYZ456/embed/captioned/?hl=en" in urls


def test_scrape_instagram_recipe_falls_back_to_embed():
    primary_html = "<html><head><meta property='og:description' content=''></head></html>"
    embed_html = """
    <html>
      <head>
        <meta property="og:description" content='chef on Instagram: "Quick Reel Recipe\\nIngredients:\\n1 lb chicken\\nInstructions:\\nCook."' />
        <meta property="og:image" content="https://example.com/reel.jpg" />
      </head>
    </html>
    """

    first_resp = Mock()
    first_resp.text = primary_html
    first_resp.raise_for_status = Mock()

    second_resp = Mock()
    second_resp.text = embed_html
    second_resp.raise_for_status = Mock()

    with patch("backend.scraper.requests.get", side_effect=[first_resp, second_resp]) as mock_get:
        recipe = _scrape_instagram_recipe("https://www.instagram.com/reel/XYZ456/")

    assert mock_get.call_count == 2
    assert recipe["title"] == "Quick Reel Recipe"
    assert recipe["image_url"] == "https://example.com/reel.jpg"
    assert recipe["ingredients"]
    assert "1 lb chicken" in recipe["ingredients"][0]["items"]
