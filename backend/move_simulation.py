import random
import time
import requests

ASSET_IDS = [1, 2]  # Match your database IDs

def simulate_movement():
    while True:
        for asset_id in ASSET_IDS:
            lon = 79.80 + random.random() * 0.1
            lat = 6.85 + random.random() * 0.1
            try:
                requests.put(
                    f"http://localhost:5000/api/assets/{asset_id}",
                    json={"longitude": lon, "latitude": lat},
                    timeout=2
                )
                print(f"Updated asset {asset_id} to {lat:.4f}, {lon:.4f}")
            except requests.RequestException as e:
                print(f"Error updating asset {asset_id}: {e}")
        time.sleep(10)

if __name__ == '__main__':
    simulate_movement()