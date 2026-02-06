# Recipe Collection Website Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a personal recipe scraper website where you and your partner can save recipes from URLs, track cooking status, and add ratings/notes.

**Architecture:** Python Flask backend with recipe-scrapers library for URL scraping, Supabase PostgreSQL for storage, vanilla JavaScript frontend with basic password protection. Start with local hosting, designed for future cloud deployment.

**Tech Stack:** Python 3.10+, Flask, recipe-scrapers, Supabase (PostgreSQL), vanilla JavaScript, HTML/CSS

---

## Task 1: Project Setup and Dependencies

**Files:**
- Create: `backend/requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`

**Step 1: Create .gitignore**

```bash
echo "venv/
__pycache__/
*.pyc
.env
.pytest_cache/
*.db
node_modules/" > .gitignore
```

**Step 2: Create project structure**

```bash
mkdir -p backend frontend tests docs/plans
```

**Step 3: Create requirements.txt**

Create `backend/requirements.txt`:

```txt
flask==3.0.0
flask-cors==4.0.0
recipe-scrapers==14.52.0
supabase==2.3.0
python-dotenv==1.0.0
pytest==7.4.3
requests==2.31.0
```

**Step 4: Create .env.example**

Create `.env.example`:

```env
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here
APP_PASSWORD=your_shared_password_here
SECRET_KEY=your_flask_secret_key_here
```

**Step 5: Create virtual environment and install dependencies**

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Expected: All packages install successfully

**Step 6: Commit**

```bash
git init
git add .
git commit -m "chore: initial project setup with dependencies"
```

---

## Task 2: Supabase Setup and Database Schema

**Files:**
- Create: `backend/database.py`
- Create: `backend/schema.sql`
- Create: `tests/test_database.py`

**Step 1: Write the failing test**

Create `tests/test_database.py`:

```python
import pytest
from backend.database import get_supabase_client

def test_supabase_connection():
    """Test that we can connect to Supabase"""
    client = get_supabase_client()
    assert client is not None
    # Try a simple query to verify connection
    result = client.table('recipes').select('count').execute()
    assert result is not None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_database.py::test_supabase_connection -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'backend.database'"

**Step 3: Create database module**

Create `backend/database.py`:

```python
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def get_supabase_client() -> Client:
    """Create and return Supabase client"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")

    return create_client(url, key)
```

**Step 4: Create database schema**

Create `backend/schema.sql`:

```sql
-- Recipe collection table
CREATE TABLE IF NOT EXISTS recipes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    image_url TEXT,
    ingredients JSONB,
    instructions TEXT,
    total_time INTEGER, -- in minutes
    yields TEXT, -- e.g., "4 servings"
    status TEXT CHECK (status IN ('want_to_cook', 'already_cooked')) DEFAULT 'want_to_cook',
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    notes TEXT,
    date_cooked TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for faster queries
CREATE INDEX idx_recipes_status ON recipes(status);
CREATE INDEX idx_recipes_created_at ON recipes(created_at DESC);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_recipes_updated_at BEFORE UPDATE ON recipes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

**Step 5: Manual step - Set up Supabase**

1. Go to https://supabase.com and create a free account
2. Create a new project
3. Go to SQL Editor and run the contents of `backend/schema.sql`
4. Copy your Project URL and anon public key
5. Create `.env` file based on `.env.example` and add your credentials

**Step 6: Run test to verify it passes**

Run: `pytest tests/test_database.py::test_supabase_connection -v`

Expected: PASS (after you've set up .env with real credentials)

**Step 7: Commit**

```bash
git add backend/database.py backend/schema.sql tests/test_database.py
git commit -m "feat: add Supabase connection and database schema"
```

---

## Task 3: Recipe Scraper Service

**Files:**
- Create: `backend/scraper.py`
- Create: `tests/test_scraper.py`

**Step 1: Write the failing test**

Create `tests/test_scraper.py`:

```python
import pytest
from backend.scraper import scrape_recipe

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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_scraper.py -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'backend.scraper'"

**Step 3: Write minimal implementation**

Create `backend/scraper.py`:

```python
from recipe_scrapers import scrape_me_now
from typing import Dict, Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def scrape_recipe(url: str) -> Dict:
    """
    Scrape recipe data from a URL using recipe-scrapers library

    Args:
        url: The recipe URL to scrape

    Returns:
        Dictionary containing recipe data

    Raises:
        ValueError: If URL is invalid
        Exception: If scraping fails
    """
    if not url or not url.startswith('http'):
        raise ValueError("Invalid URL provided")

    try:
        # Use wild_mode to support sites following common patterns
        scraper = scrape_me_now(url, wild_mode=True)

        # Extract recipe data
        recipe_data = {
            'url': url,
            'title': scraper.title(),
            'image_url': scraper.image() if scraper.image() else None,
            'ingredients': scraper.ingredients(),
            'instructions': scraper.instructions(),
            'total_time': scraper.total_time() if scraper.total_time() else None,
            'yields': scraper.yields() if scraper.yields() else None,
        }

        logger.info(f"Successfully scraped recipe: {recipe_data['title']}")
        return recipe_data

    except Exception as e:
        logger.error(f"Failed to scrape recipe from {url}: {str(e)}")
        raise Exception(f"Failed to scrape recipe: {str(e)}")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_scraper.py::test_scrape_recipe_success -v`

Expected: PASS (requires internet connection)

**Step 5: Run all scraper tests**

Run: `pytest tests/test_scraper.py -v`

Expected: test_scrape_recipe_success PASS, test_scrape_recipe_invalid_url PASS, test_scrape_recipe_with_wild_mode might SKIP or PASS

**Step 6: Commit**

```bash
git add backend/scraper.py tests/test_scraper.py
git commit -m "feat: add recipe scraper service with wild_mode support"
```

---

## Task 4: Password Authentication Middleware

**Files:**
- Create: `backend/auth.py`
- Create: `tests/test_auth.py`

**Step 1: Write the failing test**

Create `tests/test_auth.py`:

```python
import pytest
from flask import Flask, session
from backend.auth import check_password, login_required

def test_check_password_correct():
    """Test that correct password returns True"""
    # We'll use a test password
    assert check_password("testpassword", "testpassword") == True

def test_check_password_incorrect():
    """Test that incorrect password returns False"""
    assert check_password("wrongpassword", "testpassword") == False

def test_login_required_decorator():
    """Test that login_required blocks unauthenticated requests"""
    app = Flask(__name__)
    app.secret_key = 'test_secret'

    @app.route('/protected')
    @login_required
    def protected_route():
        return 'Access granted'

    with app.test_client() as client:
        # Without login, should return 401
        response = client.get('/protected')
        assert response.status_code == 401

        # With login session
        with client.session_transaction() as sess:
            sess['authenticated'] = True

        response = client.get('/protected')
        assert response.status_code == 200
        assert b'Access granted' in response.data
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_auth.py -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'backend.auth'"

**Step 3: Write minimal implementation**

Create `backend/auth.py`:

```python
import os
from functools import wraps
from flask import session, jsonify, request
from dotenv import load_dotenv

load_dotenv()

def check_password(provided_password: str, correct_password: str = None) -> bool:
    """
    Check if provided password matches the configured password

    Args:
        provided_password: Password provided by user
        correct_password: Override password (for testing), defaults to env var

    Returns:
        True if password matches, False otherwise
    """
    if correct_password is None:
        correct_password = os.getenv('APP_PASSWORD')

    return provided_password == correct_password

def login_required(f):
    """
    Decorator to require authentication for routes
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_auth.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add backend/auth.py tests/test_auth.py
git commit -m "feat: add password authentication middleware"
```

---

## Task 5: Flask API Endpoints

**Files:**
- Create: `backend/app.py`
- Create: `tests/test_api.py`

**Step 1: Write the failing test**

Create `tests/test_api.py`:

```python
import pytest
import json
from backend.app import create_app

@pytest.fixture
def client():
    """Create test client"""
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api.py -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'backend.app'"

**Step 3: Write minimal implementation**

Create `backend/app.py`:

```python
import os
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from dotenv import load_dotenv
from backend.database import get_supabase_client
from backend.scraper import scrape_recipe
from backend.auth import check_password, login_required

load_dotenv()

def create_app():
    """Create and configure Flask app"""
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Enable CORS for local development
    CORS(app, supports_credentials=True)

    # Get Supabase client
    supabase = get_supabase_client()

    @app.route('/api/login', methods=['POST'])
    def login():
        """Login endpoint - check password"""
        data = request.get_json()
        password = data.get('password')

        if check_password(password):
            session['authenticated'] = True
            return jsonify({'success': True, 'message': 'Login successful'}), 200

        return jsonify({'error': 'Invalid password'}), 401

    @app.route('/api/logout', methods=['POST'])
    def logout():
        """Logout endpoint"""
        session.pop('authenticated', None)
        return jsonify({'success': True, 'message': 'Logged out'}), 200

    @app.route('/api/recipes', methods=['GET'])
    @login_required
    def list_recipes():
        """Get all recipes"""
        try:
            result = supabase.table('recipes').select('*').order('created_at', desc=True).execute()
            return jsonify(result.data), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/recipes', methods=['POST'])
    @login_required
    def add_recipe():
        """Add a new recipe from URL"""
        try:
            data = request.get_json()
            url = data.get('url')

            if not url:
                return jsonify({'error': 'URL is required'}), 400

            # Check if recipe already exists
            existing = supabase.table('recipes').select('id').eq('url', url).execute()
            if existing.data:
                return jsonify({'error': 'Recipe already exists', 'id': existing.data[0]['id']}), 409

            # Scrape recipe
            recipe_data = scrape_recipe(url)

            # Insert into database
            result = supabase.table('recipes').insert(recipe_data).execute()

            return jsonify(result.data[0]), 201

        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': f'Failed to add recipe: {str(e)}'}), 500

    @app.route('/api/recipes/<recipe_id>', methods=['PUT'])
    @login_required
    def update_recipe(recipe_id):
        """Update recipe status, rating, or notes"""
        try:
            data = request.get_json()

            # Build update object with only provided fields
            update_data = {}
            if 'status' in data:
                if data['status'] not in ['want_to_cook', 'already_cooked']:
                    return jsonify({'error': 'Invalid status'}), 400
                update_data['status'] = data['status']

            if 'rating' in data:
                rating = data['rating']
                if rating is not None and (rating < 1 or rating > 5):
                    return jsonify({'error': 'Rating must be between 1 and 5'}), 400
                update_data['rating'] = rating

            if 'notes' in data:
                update_data['notes'] = data['notes']

            if 'date_cooked' in data:
                update_data['date_cooked'] = data['date_cooked']

            if not update_data:
                return jsonify({'error': 'No fields to update'}), 400

            # Update in database
            result = supabase.table('recipes').update(update_data).eq('id', recipe_id).execute()

            if not result.data:
                return jsonify({'error': 'Recipe not found'}), 404

            return jsonify(result.data[0]), 200

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/recipes/<recipe_id>', methods=['DELETE'])
    @login_required
    def delete_recipe(recipe_id):
        """Delete a recipe"""
        try:
            result = supabase.table('recipes').delete().eq('id', recipe_id).execute()

            if not result.data:
                return jsonify({'error': 'Recipe not found'}), 404

            return jsonify({'success': True, 'message': 'Recipe deleted'}), 200

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/health', methods=['GET'])
    def health():
        """Health check endpoint"""
        return jsonify({'status': 'healthy'}), 200

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_api.py -v`

Expected: PASS (requires .env with real Supabase credentials)

**Step 5: Manual test - Start the server**

Run: `python backend/app.py`

Expected: Server starts on http://localhost:5000

Test with curl:
```bash
curl http://localhost:5000/api/health
```

Expected: {"status": "healthy"}

**Step 6: Commit**

```bash
git add backend/app.py tests/test_api.py
git commit -m "feat: add Flask API with recipe endpoints and auth"
```

---

## Task 6: Frontend Interface

**Files:**
- Create: `frontend/index.html`
- Create: `frontend/styles.css`
- Create: `frontend/app.js`

**Step 1: Create HTML structure**

Create `frontend/index.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Our Recipe Collection</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <!-- Login Screen -->
    <div id="login-screen" class="screen active">
        <div class="login-container">
            <h1>🍳 Our Recipe Collection</h1>
            <p>Welcome! Enter the password to continue.</p>
            <form id="login-form">
                <input type="password" id="password-input" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
            <div id="login-error" class="error"></div>
        </div>
    </div>

    <!-- Main App Screen -->
    <div id="app-screen" class="screen">
        <header>
            <h1>🍳 Our Recipe Collection</h1>
            <button id="logout-btn" class="logout-btn">Logout</button>
        </header>

        <main>
            <!-- Add Recipe Section -->
            <section class="add-recipe-section">
                <h2>Add New Recipe</h2>
                <form id="add-recipe-form">
                    <input type="url" id="recipe-url" placeholder="Paste recipe URL here..." required>
                    <button type="submit">Scrape Recipe</button>
                </form>
                <div id="scrape-status" class="status-message"></div>
            </section>

            <!-- Filter Section -->
            <section class="filter-section">
                <button class="filter-btn active" data-filter="all">All Recipes</button>
                <button class="filter-btn" data-filter="want_to_cook">Want to Cook</button>
                <button class="filter-btn" data-filter="already_cooked">Already Cooked</button>
            </section>

            <!-- Recipes Grid -->
            <section id="recipes-container" class="recipes-grid">
                <p class="loading">Loading recipes...</p>
            </section>
        </main>
    </div>

    <!-- Recipe Modal -->
    <div id="recipe-modal" class="modal">
        <div class="modal-content">
            <span class="close">&times;</span>
            <div id="modal-body"></div>
        </div>
    </div>

    <script src="app.js"></script>
</body>
</html>
```

**Step 2: Create CSS styles**

Create `frontend/styles.css`:

```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    color: #333;
}

/* Screen Management */
.screen {
    display: none;
}

.screen.active {
    display: block;
}

/* Login Screen */
.login-container {
    max-width: 400px;
    margin: 100px auto;
    background: white;
    padding: 40px;
    border-radius: 20px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    text-align: center;
}

.login-container h1 {
    margin-bottom: 10px;
    color: #667eea;
}

.login-container p {
    margin-bottom: 30px;
    color: #666;
}

#login-form {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

#login-form input {
    padding: 12px;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 16px;
}

#login-form button {
    padding: 12px;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    cursor: pointer;
    transition: background 0.3s;
}

#login-form button:hover {
    background: #5568d3;
}

/* Header */
header {
    background: white;
    padding: 20px 40px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

header h1 {
    color: #667eea;
    font-size: 24px;
}

.logout-btn {
    padding: 8px 16px;
    background: #f44336;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.3s;
}

.logout-btn:hover {
    background: #d32f2f;
}

/* Main Content */
main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 40px 20px;
}

/* Add Recipe Section */
.add-recipe-section {
    background: white;
    padding: 30px;
    border-radius: 15px;
    margin-bottom: 30px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}

.add-recipe-section h2 {
    margin-bottom: 20px;
    color: #667eea;
}

#add-recipe-form {
    display: flex;
    gap: 10px;
}

#recipe-url {
    flex: 1;
    padding: 12px;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 16px;
}

#add-recipe-form button {
    padding: 12px 24px;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: background 0.3s;
}

#add-recipe-form button:hover {
    background: #5568d3;
}

.status-message {
    margin-top: 15px;
    padding: 10px;
    border-radius: 6px;
}

.status-message.success {
    background: #4caf50;
    color: white;
}

.status-message.error {
    background: #f44336;
    color: white;
}

.error {
    color: #f44336;
    margin-top: 10px;
}

/* Filter Section */
.filter-section {
    display: flex;
    gap: 10px;
    margin-bottom: 30px;
    flex-wrap: wrap;
}

.filter-btn {
    padding: 10px 20px;
    background: white;
    border: 2px solid #667eea;
    color: #667eea;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s;
}

.filter-btn:hover, .filter-btn.active {
    background: #667eea;
    color: white;
}

/* Recipes Grid */
.recipes-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
}

.recipe-card {
    background: white;
    border-radius: 15px;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    transition: transform 0.3s, box-shadow 0.3s;
    cursor: pointer;
}

.recipe-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 30px rgba(0,0,0,0.15);
}

.recipe-card img {
    width: 100%;
    height: 200px;
    object-fit: cover;
}

.recipe-card-content {
    padding: 20px;
}

.recipe-card h3 {
    margin-bottom: 10px;
    color: #333;
    font-size: 18px;
}

.recipe-status {
    display: inline-block;
    padding: 5px 10px;
    border-radius: 15px;
    font-size: 12px;
    margin-bottom: 10px;
}

.recipe-status.want_to_cook {
    background: #fff3cd;
    color: #856404;
}

.recipe-status.already_cooked {
    background: #d4edda;
    color: #155724;
}

.recipe-rating {
    color: #ffa000;
    margin-bottom: 10px;
}

.recipe-notes {
    color: #666;
    font-size: 14px;
    font-style: italic;
}

.loading {
    text-align: center;
    color: white;
    font-size: 18px;
    padding: 40px;
}

/* Modal */
.modal {
    display: none;
    position: fixed;
    z-index: 1000;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.7);
    overflow: auto;
}

.modal.active {
    display: block;
}

.modal-content {
    background: white;
    margin: 50px auto;
    padding: 30px;
    max-width: 800px;
    border-radius: 15px;
    position: relative;
}

.close {
    position: absolute;
    right: 20px;
    top: 20px;
    font-size: 30px;
    font-weight: bold;
    color: #aaa;
    cursor: pointer;
}

.close:hover {
    color: #333;
}

.modal-content img {
    width: 100%;
    max-height: 400px;
    object-fit: cover;
    border-radius: 10px;
    margin-bottom: 20px;
}

.modal-content h2 {
    color: #667eea;
    margin-bottom: 20px;
}

.modal-content h3 {
    color: #333;
    margin-top: 20px;
    margin-bottom: 10px;
}

.modal-content ul {
    list-style-position: inside;
    margin-bottom: 20px;
}

.modal-content li {
    margin-bottom: 8px;
    color: #666;
}

.modal-actions {
    display: flex;
    gap: 15px;
    margin-top: 20px;
    flex-wrap: wrap;
}

.modal-actions select,
.modal-actions input,
.modal-actions textarea {
    padding: 8px;
    border: 2px solid #e0e0e0;
    border-radius: 6px;
    font-size: 14px;
}

.modal-actions textarea {
    flex: 1 1 100%;
    min-height: 60px;
    resize: vertical;
}

.modal-actions button {
    padding: 10px 20px;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.3s;
}

.modal-actions button:hover {
    background: #5568d3;
}

.modal-actions button.delete {
    background: #f44336;
}

.modal-actions button.delete:hover {
    background: #d32f2f;
}

@media (max-width: 768px) {
    .recipes-grid {
        grid-template-columns: 1fr;
    }

    #add-recipe-form {
        flex-direction: column;
    }
}
```

**Step 3: Create JavaScript app**

Create `frontend/app.js`:

```javascript
const API_URL = 'http://localhost:5000/api';

// State
let recipes = [];
let currentFilter = 'all';
let isAuthenticated = false;

// DOM Elements
const loginScreen = document.getElementById('login-screen');
const appScreen = document.getElementById('app-screen');
const loginForm = document.getElementById('login-form');
const loginError = document.getElementById('login-error');
const logoutBtn = document.getElementById('logout-btn');
const addRecipeForm = document.getElementById('add-recipe-form');
const recipeUrlInput = document.getElementById('recipe-url');
const scrapeStatus = document.getElementById('scrape-status');
const recipesContainer = document.getElementById('recipes-container');
const filterBtns = document.querySelectorAll('.filter-btn');
const recipeModal = document.getElementById('recipe-modal');
const modalClose = document.querySelector('.close');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    setupEventListeners();
});

function setupEventListeners() {
    loginForm.addEventListener('submit', handleLogin);
    logoutBtn.addEventListener('click', handleLogout);
    addRecipeForm.addEventListener('submit', handleAddRecipe);
    filterBtns.forEach(btn => {
        btn.addEventListener('click', handleFilter);
    });
    modalClose.addEventListener('click', closeModal);
    window.addEventListener('click', (e) => {
        if (e.target === recipeModal) {
            closeModal();
        }
    });
}

// Authentication
function checkAuth() {
    // Check if session is authenticated
    fetch(`${API_URL}/recipes`, {
        credentials: 'include'
    })
    .then(response => {
        if (response.ok) {
            showApp();
        } else {
            showLogin();
        }
    })
    .catch(() => showLogin());
}

async function handleLogin(e) {
    e.preventDefault();
    const password = document.getElementById('password-input').value;

    try {
        const response = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ password })
        });

        if (response.ok) {
            showApp();
        } else {
            loginError.textContent = 'Invalid password';
        }
    } catch (error) {
        loginError.textContent = 'Connection error';
    }
}

async function handleLogout() {
    try {
        await fetch(`${API_URL}/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        showLogin();
    } catch (error) {
        console.error('Logout error:', error);
    }
}

function showLogin() {
    loginScreen.classList.add('active');
    appScreen.classList.remove('active');
    isAuthenticated = false;
}

function showApp() {
    loginScreen.classList.remove('active');
    appScreen.classList.add('active');
    isAuthenticated = true;
    loadRecipes();
}

// Recipe Management
async function loadRecipes() {
    try {
        const response = await fetch(`${API_URL}/recipes`, {
            credentials: 'include'
        });

        if (response.ok) {
            recipes = await response.json();
            renderRecipes();
        } else {
            showLogin();
        }
    } catch (error) {
        recipesContainer.innerHTML = `<p class="error">Failed to load recipes: ${error.message}</p>`;
    }
}

async function handleAddRecipe(e) {
    e.preventDefault();
    const url = recipeUrlInput.value;

    scrapeStatus.textContent = 'Scraping recipe...';
    scrapeStatus.className = 'status-message';

    try {
        const response = await fetch(`${API_URL}/recipes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ url })
        });

        if (response.ok) {
            scrapeStatus.textContent = 'Recipe added successfully!';
            scrapeStatus.classList.add('success');
            recipeUrlInput.value = '';
            setTimeout(() => {
                scrapeStatus.textContent = '';
                scrapeStatus.className = 'status-message';
            }, 3000);
            loadRecipes();
        } else {
            const error = await response.json();
            scrapeStatus.textContent = error.error || 'Failed to add recipe';
            scrapeStatus.classList.add('error');
        }
    } catch (error) {
        scrapeStatus.textContent = `Error: ${error.message}`;
        scrapeStatus.classList.add('error');
    }
}

function handleFilter(e) {
    currentFilter = e.target.dataset.filter;
    filterBtns.forEach(btn => btn.classList.remove('active'));
    e.target.classList.add('active');
    renderRecipes();
}

function renderRecipes() {
    const filteredRecipes = recipes.filter(recipe => {
        if (currentFilter === 'all') return true;
        return recipe.status === currentFilter;
    });

    if (filteredRecipes.length === 0) {
        recipesContainer.innerHTML = '<p class="loading">No recipes found. Add some recipes to get started!</p>';
        return;
    }

    recipesContainer.innerHTML = filteredRecipes.map(recipe => `
        <div class="recipe-card" onclick="openRecipeModal('${recipe.id}')">
            ${recipe.image_url ? `<img src="${recipe.image_url}" alt="${recipe.title}">` : ''}
            <div class="recipe-card-content">
                <h3>${recipe.title}</h3>
                <span class="recipe-status ${recipe.status}">
                    ${recipe.status === 'want_to_cook' ? 'Want to Cook' : 'Already Cooked'}
                </span>
                ${recipe.rating ? `<div class="recipe-rating">${'⭐'.repeat(recipe.rating)}</div>` : ''}
                ${recipe.notes ? `<p class="recipe-notes">"${recipe.notes}"</p>` : ''}
            </div>
        </div>
    `).join('');
}

function openRecipeModal(recipeId) {
    const recipe = recipes.find(r => r.id === recipeId);
    if (!recipe) return;

    const ingredientsList = Array.isArray(recipe.ingredients)
        ? recipe.ingredients.map(ing => `<li>${ing}</li>`).join('')
        : '<li>No ingredients available</li>';

    const modalBody = document.getElementById('modal-body');
    modalBody.innerHTML = `
        ${recipe.image_url ? `<img src="${recipe.image_url}" alt="${recipe.title}">` : ''}
        <h2>${recipe.title}</h2>
        ${recipe.total_time ? `<p><strong>Total Time:</strong> ${recipe.total_time} minutes</p>` : ''}
        ${recipe.yields ? `<p><strong>Yields:</strong> ${recipe.yields}</p>` : ''}

        <h3>Ingredients</h3>
        <ul>${ingredientsList}</ul>

        <h3>Instructions</h3>
        <p>${recipe.instructions || 'No instructions available'}</p>

        <div class="modal-actions">
            <select id="modal-status" value="${recipe.status}">
                <option value="want_to_cook" ${recipe.status === 'want_to_cook' ? 'selected' : ''}>Want to Cook</option>
                <option value="already_cooked" ${recipe.status === 'already_cooked' ? 'selected' : ''}>Already Cooked</option>
            </select>

            <select id="modal-rating">
                <option value="">No Rating</option>
                <option value="1" ${recipe.rating === 1 ? 'selected' : ''}>⭐</option>
                <option value="2" ${recipe.rating === 2 ? 'selected' : ''}>⭐⭐</option>
                <option value="3" ${recipe.rating === 3 ? 'selected' : ''}>⭐⭐⭐</option>
                <option value="4" ${recipe.rating === 4 ? 'selected' : ''}>⭐⭐⭐⭐</option>
                <option value="5" ${recipe.rating === 5 ? 'selected' : ''}>⭐⭐⭐⭐⭐</option>
            </select>

            <textarea id="modal-notes" placeholder="Add notes...">${recipe.notes || ''}</textarea>

            <button onclick="updateRecipe('${recipe.id}')">Save Changes</button>
            <button class="delete" onclick="deleteRecipe('${recipe.id}')">Delete Recipe</button>
        </div>

        <p style="margin-top: 20px;"><a href="${recipe.url}" target="_blank">View Original Recipe</a></p>
    `;

    recipeModal.classList.add('active');
}

function closeModal() {
    recipeModal.classList.remove('active');
}

async function updateRecipe(recipeId) {
    const status = document.getElementById('modal-status').value;
    const rating = document.getElementById('modal-rating').value;
    const notes = document.getElementById('modal-notes').value;

    try {
        const response = await fetch(`${API_URL}/recipes/${recipeId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                status,
                rating: rating ? parseInt(rating) : null,
                notes,
                date_cooked: status === 'already_cooked' ? new Date().toISOString() : null
            })
        });

        if (response.ok) {
            closeModal();
            loadRecipes();
        } else {
            alert('Failed to update recipe');
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

async function deleteRecipe(recipeId) {
    if (!confirm('Are you sure you want to delete this recipe?')) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/recipes/${recipeId}`, {
            method: 'DELETE',
            credentials: 'include'
        });

        if (response.ok) {
            closeModal();
            loadRecipes();
        } else {
            alert('Failed to delete recipe');
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}
```

**Step 4: Test the frontend manually**

1. Make sure backend is running: `python backend/app.py`
2. Open `frontend/index.html` in a browser
3. Test login with password from .env
4. Test adding a recipe URL
5. Test filtering recipes
6. Test updating recipe status, rating, and notes
7. Test deleting a recipe

**Step 5: Commit**

```bash
git add frontend/
git commit -m "feat: add frontend interface with login and recipe management"
```

---

## Task 7: Documentation and Deployment Setup

**Files:**
- Create: `README.md`
- Create: `backend/config.py`
- Update: `.env.example`

**Step 1: Create README**

Create `README.md`:

```markdown
# Recipe Collection Website

A personal recipe scraper website for collecting and organizing recipes from the web.

## Features

- 🔍 Scrape recipes from any URL using recipe-scrapers library
- 📝 Track cooking status (want to cook / already cooked)
- ⭐ Rate recipes (1-5 stars)
- 💬 Add personal notes to recipes
- 🔐 Password-protected access
- 📱 Responsive design

## Tech Stack

- **Backend:** Python, Flask, recipe-scrapers
- **Database:** Supabase (PostgreSQL)
- **Frontend:** Vanilla JavaScript, HTML, CSS
- **Hosting:** Local (with plans for cloud deployment)

## Setup Instructions

### Prerequisites

- Python 3.10+
- Supabase account (free tier)

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd valentines
```

2. Set up Python virtual environment:
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # On Windows
# or
source venv/bin/activate  # On Mac/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up Supabase:
   - Create account at https://supabase.com
   - Create a new project
   - Go to SQL Editor and run the schema from `backend/schema.sql`
   - Copy your Project URL and anon public key

5. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Add your Supabase credentials
   - Set a strong password for `APP_PASSWORD`
   - Generate a random secret key for `SECRET_KEY`

### Running Locally

1. Start the backend server:
```bash
cd backend
python app.py
```

The API will be available at http://localhost:5000

2. Open the frontend:
   - Open `frontend/index.html` in your web browser
   - Or use a local server: `python -m http.server 8000` from the frontend directory

3. Login with the password you set in `.env`

## Usage

1. **Add Recipe:** Paste a recipe URL and click "Scrape Recipe"
2. **View Recipes:** All recipes are displayed in a grid
3. **Filter:** Click filter buttons to show "Want to Cook" or "Already Cooked"
4. **Edit Recipe:** Click on any recipe card to open details
5. **Update Status/Rating/Notes:** Make changes in the modal and click "Save Changes"
6. **Delete Recipe:** Click "Delete Recipe" in the modal

## Supported Recipe Sites

The app uses `recipe-scrapers` library with `wild_mode` enabled, which supports:
- 100+ explicitly supported sites (AllRecipes, Food Network, NYT Cooking, etc.)
- Many other sites that follow common recipe schema patterns

## Future Enhancements

- [ ] Deploy to cloud hosting (Railway, Render, etc.)
- [ ] Add recipe search functionality
- [ ] Add tags/categories
- [ ] Export recipes to PDF
- [ ] Shopping list generation
- [ ] Meal planning features

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Project Structure

```
valentines/
├── backend/
│   ├── app.py              # Flask application
│   ├── auth.py             # Authentication middleware
│   ├── scraper.py          # Recipe scraping service
│   ├── database.py         # Supabase connection
│   ├── schema.sql          # Database schema
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── index.html          # Main HTML
│   ├── styles.css          # Styles
│   └── app.js              # Frontend JavaScript
├── tests/                  # Test files
└── docs/plans/             # Implementation plans
```

## License

Personal project - not licensed for public use.
```

**Step 2: Update .env.example with all required variables**

Update `.env.example`:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url_here
SUPABASE_KEY=your_supabase_anon_key_here

# Application Configuration
APP_PASSWORD=your_shared_password_here
SECRET_KEY=generate_a_random_secret_key_here

# Optional: Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
```

**Step 3: Create a simple run script for convenience**

Create `run.sh` (for Mac/Linux):

```bash
#!/bin/bash
cd backend
source venv/bin/activate
python app.py
```

Create `run.bat` (for Windows):

```batch
@echo off
cd backend
call venv\Scripts\activate
python app.py
```

Make executable:
```bash
chmod +x run.sh  # On Mac/Linux
```

**Step 4: Commit**

```bash
git add README.md .env.example run.sh run.bat
git commit -m "docs: add README and deployment setup"
```

---

## Task 8: Final Testing and Verification

**Step 1: Run all tests**

```bash
cd backend
pytest tests/ -v --tb=short
```

Expected: All tests pass

**Step 2: Manual end-to-end test**

1. Start backend: `python backend/app.py`
2. Open frontend in browser
3. Test complete workflow:
   - Login with password
   - Add a recipe from a popular site (e.g., AllRecipes)
   - Verify recipe appears in grid
   - Click on recipe to open modal
   - Update status to "Already Cooked"
   - Add a rating (5 stars)
   - Add notes
   - Save changes
   - Verify changes persist after page refresh
   - Test filters
   - Delete the test recipe

**Step 3: Check all files are tracked**

```bash
git status
```

Expected: All important files are committed, only venv and .env are untracked

**Step 4: Final commit**

```bash
git add .
git commit -m "chore: final verification and testing complete"
```

---

## Deployment Notes (For Future)

When ready to deploy to cloud:

### Option 1: Railway
1. Connect GitHub repo
2. Set environment variables in Railway dashboard
3. Railway will auto-detect Flask app
4. Update frontend API_URL to Railway URL

### Option 2: Render
1. Create new Web Service
2. Connect GitHub repo
3. Build command: `pip install -r backend/requirements.txt`
4. Start command: `cd backend && python app.py`
5. Add environment variables
6. Update frontend API_URL

### Frontend Hosting
- Deploy to Netlify, Vercel, or GitHub Pages
- Update API_URL to production backend URL
- Ensure CORS is configured correctly

---

## Summary

This implementation creates a fully functional recipe collection website with:

✅ Recipe scraping from any URL (using recipe-scrapers)
✅ PostgreSQL database (Supabase)
✅ Status tracking (want to cook / already cooked)
✅ Ratings and notes
✅ Password protection
✅ Responsive frontend interface
✅ Local hosting with easy cloud migration path
✅ Comprehensive tests
✅ Clear documentation

**Total estimated development time:** 3-4 hours for a skilled developer following this plan.

**Key principles applied:**
- TDD: Tests written before implementation
- DRY: No code duplication
- YAGNI: Only essential features, no over-engineering
- Frequent commits: After each major task completion
