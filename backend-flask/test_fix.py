import requests
import json

def test_chat():
    url = 'http://127.0.0.1:5000/api/chat'
    
    # Test 1: English Refusal
    print("\n--- TEST 1: English Off-Topic ---")
    payload = {'message': "What is the capital of France?"}
    try:
        r = requests.post(url, json=payload)
        print(f"Status: {r.status_code}")
        data = r.json()
        print(f"Reply: {data.get('reply')}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 2: Indonesian Refusal
    print("\n--- TEST 2: Indonesian Off-Topic ---")
    payload = {'message': "Siapa presiden amerika?"}
    try:
        r = requests.post(url, json=payload)
        print(f"Status: {r.status_code}")
        data = r.json()
        print(f"Reply: {data.get('reply')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_chat()



