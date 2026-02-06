import pytest
import json
import os
from backend.app import create_app

@pytest.fixture
def client():
    """Create test client"""
    os.environ['APP_PASSWORD'] = 'testpassword'
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def authenticated_client(client):
    """Create authenticated test client"""
    with client.session_transaction() as sess:
        sess['authenticated'] = True
    return client

def test_login_success(client):
    """Test successful login"""
    response = client.post('/api/login',
        json={'password': 'testpassword'})
    assert response.status_code == 200
    assert b'success' in response.data

def test_login_failure(client):
    """Test failed login"""
    response = client.post('/api/login',
        json={'password': 'wrongpassword'})
    assert response.status_code == 401

def test_add_recipe(authenticated_client):
    """Test adding a recipe"""
    response = authenticated_client.post('/api/recipes',
        json={'url': 'https://www.allrecipes.com/recipe/12151/banana-cream-pie-i/'})
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'id' in data
    assert data['title'] is not None

def test_preview_requires_auth(client):
    """Preview endpoint should require an authenticated session"""
    response = client.post('/api/recipes/preview',
        json={'url': 'https://www.allrecipes.com/recipe/12151/banana-cream-pie-i/'})
    assert response.status_code == 401

def test_list_recipes(authenticated_client):
    """Test listing recipes"""
    response = authenticated_client.get('/api/recipes')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)

def test_update_recipe(authenticated_client):
    """Test updating recipe status and notes"""
    # First add a recipe
    add_response = authenticated_client.post('/api/recipes',
        json={'url': 'https://www.allrecipes.com/recipe/12151/banana-cream-pie-i/'})
    recipe_id = json.loads(add_response.data)['id']

    # Update it
    response = authenticated_client.put(f'/api/recipes/{recipe_id}',
        json={
            'status': 'already_cooked',
            'rating': 5,
            'notes': 'Delicious!'
        })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'already_cooked'
    assert data['rating'] == 5


def test_update_recipe_content_fields(authenticated_client):
    """Test updating editable recipe content fields"""
    add_response = authenticated_client.post('/api/recipes/manual',
        json={
            'title': 'Edit Test Recipe',
            'ingredients': [{'section': 'Ingredients', 'items': ['Chicken thighs, 4']}],
            'instructions': 'Step 1\nCook the chicken.',
            'total_time': 30,
            'yields': '4 servings',
            'image_url': 'https://example.com/original.jpg'
        })
    assert add_response.status_code == 201
    recipe_id = json.loads(add_response.data)['id']

    update_response = authenticated_client.put(f'/api/recipes/{recipe_id}',
        json={
            'title': 'Edited Chicken Recipe',
            'ingredients': [{'section': 'Sauce', 'items': ['Greek yogurt, 100 g']}],
            'instructions': 'Step 1\nMix sauce.',
            'total_time': 12,
            'yields': '2 servings',
            'image_url': 'https://example.com/updated.jpg'
        })

    assert update_response.status_code == 200
    data = json.loads(update_response.data)
    assert data['title'] == 'Edited Chicken Recipe'
    assert data['instructions'] == 'Step 1\nMix sauce.'
    assert data['total_time'] == 12
    assert data['yields'] == '2 servings'
    assert data['image_url'] == 'https://example.com/updated.jpg'
    assert data['ingredients'][0]['section'] == 'Sauce'
