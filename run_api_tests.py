import requests
import json

base_url = "http://localhost:8000"

def test_api():
    print("Testing Health...")
    r = requests.get(f"{base_url}/health")
    print(r.status_code, r.json())
    
    print("\nTesting Risk Health...")
    r = requests.get(f"{base_url}/api/v1/risk/health")
    print(r.status_code, r.json())
    
    print("\nTesting Analyze (Valid)...")
    payload = {
        "transaction_id": "TX-TEST-001",
        "Amount": 1500.0,
        "Time": 3600.0,
        "V1": -1.2, "V2": 2.5
    }
    r = requests.post(f"{base_url}/api/v1/risk/analyze", json=payload)
    print(r.status_code, r.json())
    
    print("\nTesting Analyze (Missing Fields)...")
    r = requests.post(f"{base_url}/api/v1/risk/analyze", json={"transaction_id": "TX-TEST-002"})
    print(r.status_code, r.json())
    
    print("\nTesting Investigate...")
    r = requests.post(f"{base_url}/api/v1/risk/investigate", json=payload)
    print(r.status_code, r.json())

    print("\nTesting History...")
    r = requests.get(f"{base_url}/api/v1/risk/history")
    print(r.status_code, "Count:", len(r.json()))
    
    print("\nTesting Analytics...")
    r = requests.get(f"{base_url}/api/v1/risk/analytics")
    print(r.status_code, r.json())

if __name__ == "__main__":
    test_api()
