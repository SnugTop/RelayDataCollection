import requests
import pandas as pd
import time

def fetch_relay_fingerprints():
    """Fetch a list of relay fingerprints."""
    limit = 5000  # Maximum allowed by the Onionoo API
    offset = 0
    fingerprints = []

    while True:
        url = f'https://onionoo.torproject.org/summary?limit={limit}&offset={offset}'
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            raise Exception("Failed to fetch relay fingerprints")

        data = response.json()
        relays = data.get('relays', [])

        if not relays:
            print("No relays found in the response.")
            break

        # Ensure each relay has a 'fingerprint' key before accessing
        for relay in relays:
            # Check for 'fingerprint' or fallback key 'f'
            fingerprint = relay.get('fingerprint') or relay.get('f')
            if fingerprint:
                fingerprints.append(fingerprint)
            else:
                print(f"Warning: 'fingerprint' key not found in relay data: {relay}")

        if len(relays) < limit:
            break
        offset += limit
        time.sleep(1)  # Avoid overloading the server

    return fingerprints

def save_fingerprints_to_csv(fingerprints, filename='relay_fingerprints.csv'):
    """Save fingerprints to CSV."""
    df = pd.DataFrame(fingerprints, columns=['Fingerprint'])
    df.to_csv(filename, index=False)
    print(f"Saved {len(fingerprints)} fingerprints to {filename}")

if __name__ == "__main__":
    fingerprints = fetch_relay_fingerprints()
    save_fingerprints_to_csv(fingerprints)
