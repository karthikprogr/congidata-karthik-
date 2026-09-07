import requests, time, random

STREAM_ID = "1394e2e4-6f9"
API_KEY   = "91175771990840ec8a454cc74d98e985"
URL       = f"http://localhost:8000/api/ingest/{STREAM_ID}"

print(f"Streaming to {URL}")
print("Press Ctrl+C to stop\n")

while True:
    r = requests.post(URL,
        json={
            "revenue": round(random.uniform(500, 5000), 2),
            "units":   random.randint(1, 100),
            "profit":  round(random.uniform(100, 1500), 2),
        },
        headers={"X-Stream-Key": API_KEY}
    )
    print(f"Sent → total rows: {r.json().get('total', '?')}")
    time.sleep(0.5)
