import os
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

    @app.route('/api/recipes/<recipe_id>', methods=['PUT'])
    @login_required
    def update_recipe(recipe_id):
        """Update recipe status, rating, or notes"""
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
