import pytest
from backend.scraper import scrape_recipe, _post_process_grouped_ingredients

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
