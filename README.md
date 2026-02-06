# Recipe Collection Website

A personal recipe scraper website for collecting and organizing recipes from the web.

## Features

- Scrape recipes from any URL using recipe-scrapers library
- Preview scraped recipes before saving, with quick edits
- Edit saved recipe details (title, ingredients, instructions, yields, timing)
- Search by ingredient using normalized aliases (e.g., "chicken thighs" matches "chicken")
- Scale recipe ingredients and yields (half, double, or custom multiplier)
- Track cooking status (want to cook / already cooked)
- Rate recipes (1-5 stars)
- Add personal notes to recipes
- Password-protected access
- Responsive design

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

## Deploy (Cloud Run)

Deploy the full application (frontend + backend) to Google Cloud Run.

### 1. Deploy to Cloud Run

From repo root:

```bash
gcloud run deploy recipe-scraper \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

Set Cloud Run environment variables:
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `APP_PASSWORD`
- `SECRET_KEY`
- `FLASK_DEBUG=False`

### 2. Verify Deployment

After deployment, verify:
- Login works
- Recipe list loads
- Add/update/delete recipe endpoints work

## Usage

1. **Add Recipe:** Paste a recipe URL, review the preview, edit if needed, then save
2. **View Recipes:** All recipes are displayed in a grid
3. **Filter:** Click filter buttons to show "Want to Cook" or "Already Cooked"
4. **Search:** Choose Recipe Name or Ingredient mode to find recipes
5. **Edit Recipe Details:** Open a recipe, click "Edit Recipe Details", update fields, and save
6. **Scale Recipe:** In the recipe modal, use Half / 1x / Double or set a custom multiplier
7. **Update Status/Rating/Notes:** Make changes in the details modal and click "Save Changes"
8. **Delete Recipe:** Click "Delete Recipe" in the modal

## Supported Recipe Sites

The app uses `recipe-scrapers` library with `wild_mode` enabled, which supports:
- 100+ explicitly supported sites (AllRecipes, Food Network, NYT Cooking, etc.)
- Many other sites that follow common recipe schema patterns
- Public Instagram post links are supported with caption parsing fallback
- Public Instagram **post and reel** links are supported with caption parsing fallback

### Instagram Notes

- Instagram scraping works best for **public** posts where the recipe is in the caption.
- Captions are parsed heuristically, so formatting quality depends on how the post author structured ingredients/instructions.
- If a caption is incomplete or blocked, use **Add Recipe Manually** in the app.

## Future Enhancements

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
