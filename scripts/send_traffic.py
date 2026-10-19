"""Send N varied /predict requests (cross-platform; for Prometheus/Grafana demo).

Usage: python scripts/send_traffic.py [base_url] [count]
Example: python scripts/send_traffic.py http://localhost:8080 100
"""
import random
import sys
import time

import requests

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
COUNT = int(sys.argv[2]) if len(sys.argv) > 2 else 100


def main() -> None:
    ok = 0
    for _ in range(COUNT):
        body = {
            "age": random.randint(30, 75), "sex": random.randint(0, 1),
            "cp": random.randint(1, 4), "trestbps": random.randint(100, 180),
            "chol": random.randint(150, 350), "fbs": random.randint(0, 1),
            "restecg": random.randint(0, 2), "thalach": random.randint(100, 190),
            "exang": random.randint(0, 1),
            "oldpeak": round(random.uniform(0, 4), 1),
            "slope": random.randint(1, 3), "ca": random.randint(0, 3),
            "thal": random.choice([3, 6, 7]),
        }
        r = requests.post(f"{BASE}/predict", json=body, timeout=10)
        ok += r.status_code == 200
        time.sleep(0.05)
    print(f"{ok}/{COUNT} requests succeeded")


if __name__ == "__main__":
    main()
