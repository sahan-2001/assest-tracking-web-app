INSERT INTO assets (name, asset_type, geom)
VALUES 
('Truck 1', 'vehicle', ST_SetSRID(ST_MakePoint(79.88, 6.90), 4326)),
('Van 2', 'vehicle', ST_SetSRID(ST_MakePoint(79.87, 6.91), 4326)),
('Bike 3', 'vehicle', ST_SetSRID(ST_MakePoint(79.89, 6.89), 4326)),
('Worker A', 'personnel', ST_SetSRID(ST_MakePoint(79.86, 6.92), 4326)),
('Drone X', 'equipment', ST_SetSRID(ST_MakePoint(79.90, 6.88), 4326));
