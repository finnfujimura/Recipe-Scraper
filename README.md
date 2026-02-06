# Recipe Collection Website

A personal recipe scraper website for collecting and organizing recipes from the web.

## Features

- Scrape recipes from any URL using recipe-scrapers library
- Preview scraped recipes before saving, with quick edits
- Edit saved recipe details (title, ingredients, instructions, yields, timing)
- Search by ingredient using normalized aliases (e.g., "chicken thighs" matches "chicken")
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


## License

Personal project - not licensed for public use.
