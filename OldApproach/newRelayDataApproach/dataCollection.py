import requests
from datetime import datetime, timezone
import pandas as pd
import time

def fetch_all_bandwidth_data():
    limit = 5000  # Maximum allowed by the Onionoo API
    offset = 0
    all_bandwidth_data = []
    while True:
        url = f'https://onionoo.torproject.org/bandwidth?type=relay&limit={limit}&offset={offset}'
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch bandwidth data: {response.status_code}")
        data = response.json()
        relays = data.get('relays', [])
        if not relays:
            break
        all_bandwidth_data.extend(relays)
        if len(relays) < limit:
            break
        offset += limit
        time.sleep(1)  # Sleep to avoid overloading the server
    return all_bandwidth_data

def extract_bandwidth_data(relay):
    fingerprint = relay.get('fingerprint')
    write_history = relay.get('write_history')
    read_history = relay.get('read_history')
    if not write_history and not read_history:
        return []

    data_points = []

    # For write_history and read_history
    for history, data_type in [(write_history, 'Write'), (read_history, 'Read')]:
        if not history:
            continue
        # Use '3_months' data
        data = history.get('3_months')
        if not data:
            continue
        interval_factor = data.get("factor", 1)
        interval_start = datetime.strptime(data["first"], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
        interval_values = data["values"]
        interval_duration = data["interval"]

        for i, value in enumerate(interval_values):
            timestamp = interval_start + pd.Timedelta(seconds=i * interval_duration)
            data_points.append({
                'Fingerprint': fingerprint,
                'Timestamp': timestamp,
                'Type': data_type,
                'Bandwidth (B/s)': value * interval_factor
            })

    return data_points

def main():
    print("Fetching bandwidth data for all relays...")
    all_bandwidth_data = fetch_all_bandwidth_data()
    all_data_points = []
    print("Extracting bandwidth data...")
    for relay in all_bandwidth_data:
        data_points = extract_bandwidth_data(relay)
        all_data_points.extend(data_points)

    # Create DataFrame
    data = pd.DataFrame(all_data_points)
    # Remove timezone info
    data['Timestamp'] = pd.to_datetime(data['Timestamp']).dt.tz_localize(None)

    # Save to CSV
    print("Saving data to CSV...")
    data.to_csv('relay_bandwidth_data.csv', index=False)
    print("Data collection completed and saved to 'relay_bandwidth_data.csv'.")

if __name__ == '__main__':
    main()
