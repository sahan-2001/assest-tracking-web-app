CREATE TABLE assets (
  id SERIAL PRIMARY KEY,
  name TEXT,
  asset_type TEXT,
  last_seen TIMESTAMP DEFAULT NOW(),
  geom GEOMETRY(Point, 4326)
);

CREATE INDEX idx_assets_geom ON assets USING GIST (geom);

-- Check PostGIS is enabled
SELECT PostGIS_version();

-- Check table exists with data
SELECT id, name, ST_AsText(geom) FROM assets;