import random
import time
import requests

asset_ids = [1, 2, 3, 4, 5]

while True:
    for asset_id in asset_ids:
        lon = 79.80 + random.random() * 0.1
        lat = 6.85 + random.random() * 0.1
        requests.put(f"http://localhost:5000/api/assets/{asset_id}", json={"longitude": lon, "latitude": lat})
    time.sleep(10)
