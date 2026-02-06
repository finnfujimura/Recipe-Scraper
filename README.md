# Recipe Collection Website

A personal recipe scraper website for collecting and organizing recipes from the web.

## Features

- Scrape recipes from any URL using recipe-scrapers library
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

## Deploy (GitHub Pages + Cloud Run)

This project supports a split deploy:
- **Frontend:** GitHub Pages
- **Backend API:** Google Cloud Run

### 1. Deploy Backend to Cloud Run

From repo root:

```bash
gcloud run deploy valentines-api \
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
- `FRONTEND_ORIGINS=https://<your-github-username>.github.io`
- `SESSION_COOKIE_SAMESITE=None`
- `SESSION_COOKIE_SECURE=True`

Notes:
- `SESSION_COOKIE_SAMESITE=None` and `SESSION_COOKIE_SECURE=True` are required for login cookies to work when frontend and backend are on different domains.
- Add additional origins to `FRONTEND_ORIGINS` as a comma-separated list if needed.

### 2. Configure Frontend API URL

Update:
- `frontend/config.js`

Set:

```javascript
window.APP_CONFIG = {
    API_BASE_URL: "https://<your-cloud-run-service-url>"
};
```

### 3. Publish Frontend with GitHub Pages

Push repository to GitHub, then enable Pages from the repository settings.
Set Pages **Source** to **GitHub Actions** (the workflow at `.github/workflows/deploy-pages.yml` deploys `frontend/`).

If publishing from the `frontend/` directory, use a Pages workflow or build step that serves `frontend/index.html` as the site root.

After Pages is live, verify:
- Login works
- Recipe list loads
- Add/update/delete recipe endpoints work

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

- [ ] Add one-click deploy workflow for Cloud Run + GitHub Pages
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
