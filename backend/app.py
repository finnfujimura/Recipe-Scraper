import os
from uuid import uuid4
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from dotenv import load_dotenv

try:
    from backend.database import get_supabase_client
    from backend.scraper import scrape_recipe
    from backend.auth import check_password, login_required
    from backend.config import Config
except ModuleNotFoundError:
    from database import get_supabase_client
    from scraper import scrape_recipe
    from auth import check_password, login_required
    from config import Config

load_dotenv()


def _normalize_manual_ingredients(raw_ingredients):
    """Normalize manual ingredient payload into grouped structure."""
    if not isinstance(raw_ingredients, list) or not raw_ingredients:
        return None

    # Already grouped format: [{section, items}]
    if isinstance(raw_ingredients[0], dict):
        groups = []
        for group in raw_ingredients:
            section = str(group.get('section') or 'Ingredients').strip() or 'Ingredients'
            raw_items = group.get('items') if isinstance(group, dict) else []
            items = [
                str(item).strip()
                for item in (raw_items or [])
                if str(item).strip()
            ]
            if items:
                groups.append({'section': section, 'items': items})
        return groups or None

    # Flat list: ["item 1", "item 2"]
    if isinstance(raw_ingredients[0], str):
        items = [str(item).strip() for item in raw_ingredients if str(item).strip()]
        if not items:
            return None
        return [{'section': 'Ingredients', 'items': items}]

    return None


def _build_recipe_payload(data, recipe_url: str):
    """Build a normalized recipe payload for inserts."""
    title = str(data.get('title') or '').strip()
    instructions = str(data.get('instructions') or '').strip()
    normalized_ingredients = _normalize_manual_ingredients(data.get('ingredients'))

    if not title:
        raise ValueError('Title is required')
    if not instructions:
        raise ValueError('Instructions are required')
    if not normalized_ingredients:
        raise ValueError('Ingredients are required')

    total_time_raw = data.get('total_time')
    total_time = None
    if total_time_raw not in (None, ''):
        total_time = int(total_time_raw)
        if total_time < 0:
            raise ValueError('Total time must be non-negative')

    return {
        'url': recipe_url,
        'title': title,
        'image_url': str(data.get('image_url') or '').strip() or None,
        'ingredients': normalized_ingredients,
        'instructions': instructions,
        'total_time': total_time,
        'yields': str(data.get('yields') or '').strip() or None,
    }


def create_app():
    """Create and configure Flask app"""
    # Serve static files from ../frontend (absolute path)
    base_dir = os.path.abspath(os.path.dirname(__file__))
    frontend_dir = os.path.join(base_dir, '../frontend')
    app = Flask(__name__, static_folder=frontend_dir, static_url_path='')
    app.config.from_object(Config)
    app.secret_key = app.config.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    @app.route('/')
    def index():
        return app.send_static_file('index.html')

    # Enable CORS for configured frontend hosts (local + production).
    CORS(
        app,
        supports_credentials=True,
        origins=app.config.get('FRONTEND_ORIGINS', []),
    )

    # Get Supabase client
    supabase = get_supabase_client()

    @app.route('/api/login', methods=['POST'])
    def login():
        """Login endpoint - check password"""
        data = request.get_json()
        password = data.get('password') if data else None

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
            url = data.get('url') if data else None

            if not url:
                return jsonify({'error': 'URL is required'}), 400

            # Check if recipe already exists
            existing = supabase.table('recipes').select('id').eq('url', url).execute()
            if existing.data:
                return jsonify({'error': 'Recipe already exists', 'id': existing.data[0]['id']}), 409

            # Scrape recipe
            recipe_data = scrape_recipe(url)
            if recipe_data.get('error'):
                return jsonify({'error': recipe_data['error']}), 422

            # Insert into database
            result = supabase.table('recipes').insert(recipe_data).execute()

            return jsonify(result.data[0]), 201

        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': f'Failed to add recipe: {str(e)}'}), 500

    @app.route('/api/recipes/preview', methods=['POST'])
    @login_required
    def preview_recipe():
        """Scrape a recipe URL and return editable preview data without saving."""
        try:
            data = request.get_json() or {}
            url = str(data.get('url') or '').strip()
            if not url:
                return jsonify({'error': 'URL is required'}), 400

            existing = supabase.table('recipes').select('id').eq('url', url).execute()
            if existing.data:
                return jsonify({'error': 'Recipe already exists', 'id': existing.data[0]['id']}), 409

            recipe_data = scrape_recipe(url)
            if recipe_data.get('error'):
                return jsonify({'error': recipe_data['error']}), 422

            return jsonify(recipe_data), 200
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': f'Failed to preview recipe: {str(e)}'}), 500

    @app.route('/api/recipes/manual', methods=['POST'])
    @login_required
    def add_manual_recipe():
        """Add a recipe manually without scraping."""
        try:
            data = request.get_json() or {}

            source_url = str(data.get('source_url') or '').strip()
            recipe_url = f"manual://{uuid4()}"
            if source_url:
                if not source_url.startswith('http'):
                    return jsonify({'error': 'Source URL must start with http/https'}), 400
                existing = supabase.table('recipes').select('id').eq('url', source_url).execute()
                if existing.data:
                    return jsonify({'error': 'Recipe already exists', 'id': existing.data[0]['id']}), 409
                recipe_url = source_url

            recipe_data = _build_recipe_payload(data, recipe_url)
            result = supabase.table('recipes').insert(recipe_data).execute()
            return jsonify(result.data[0]), 201

        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': f'Failed to add manual recipe: {str(e)}'}), 500

    @app.route('/api/recipes/<recipe_id>', methods=['PUT'])
    @login_required
    def update_recipe(recipe_id):
        """Update recipe fields."""
        try:
            data = request.get_json() or {}

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

            # Editable recipe content fields
            if 'title' in data:
                title = str(data.get('title') or '').strip()
                if not title:
                    return jsonify({'error': 'Title is required'}), 400
                update_data['title'] = title

            if 'ingredients' in data:
                normalized_ingredients = _normalize_manual_ingredients(data.get('ingredients'))
                if not normalized_ingredients:
                    return jsonify({'error': 'Ingredients are required'}), 400
                update_data['ingredients'] = normalized_ingredients

            if 'instructions' in data:
                instructions = str(data.get('instructions') or '').strip()
                if not instructions:
                    return jsonify({'error': 'Instructions are required'}), 400
                update_data['instructions'] = instructions

            if 'total_time' in data:
                total_time_raw = data.get('total_time')
                if total_time_raw in (None, ''):
                    update_data['total_time'] = None
                else:
                    total_time = int(total_time_raw)
                    if total_time < 0:
                        return jsonify({'error': 'Total time must be non-negative'}), 400
                    update_data['total_time'] = total_time

            if 'yields' in data:
                update_data['yields'] = str(data.get('yields') or '').strip() or None

            if 'image_url' in data:
                update_data['image_url'] = str(data.get('image_url') or '').strip() or None

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
    app.run(
        debug=True,
        host='0.0.0.0',
        port=int(os.getenv('PORT', '5000')),
    )
