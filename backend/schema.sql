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
