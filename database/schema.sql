CREATE TABLE assets (
  id SERIAL PRIMARY KEY,
  name TEXT,
  asset_type TEXT,
  last_seen TIMESTAMP DEFAULT NOW(),
  geom GEOMETRY(Point, 4326)
);

CREATE INDEX idx_assets_geom ON assets USING GIST (geom);
