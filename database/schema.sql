CREATE TABLE assets (
  id SERIAL PRIMARY KEY,
  name TEXT,
  asset_type TEXT,
  last_seen TIMESTAMP DEFAULT NOW(),
  geom GEOMETRY(Point, 4326)
);

CREATE INDEX idx_assets_geom ON assets USING GIST (geom);

CREATE TABLE IF NOT EXISTS bookings (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER REFERENCES assets(id),
    user_id VARCHAR(100),
    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Check PostGIS is enabled
SELECT PostGIS_version();

-- Check table exists with data
SELECT id, name, ST_AsText(geom) FROM assets;