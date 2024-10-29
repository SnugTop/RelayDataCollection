import requests
from datetime import datetime, timezone, timedelta
import pandas as pd
import time

def fetch_all_bandwidth_data():
    limit = 5000  # Maximum allowed by the Onionoo API
    offset = 0
    all_bandwidth_data = []
    one_month_ago = (datetime.now(timezone.utc) - timedelta(days=30)).strftime('%Y-%m-%d')
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    while True:
        # Query with a strict time range for daily data from one month ago to today
        url = f'https://onionoo.torproject.org/bandwidth?type=relay&limit={limit}&offset={offset}&start={one_month_ago}&end={today}'
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
    end_date = datetime.now(timezone.utc) - timedelta(days=30)  # End one month ago from today
    start_date = end_date - timedelta(days=30)  # Start two months ago

    # For write_history and read_history
    for history, data_type in [(write_history, 'Write'), (read_history, 'Read')]:
        if not history:
            continue
        data = history.get("1_month") or history.get("3_months") or history.get("1_week")
        if not data:
            continue

        interval_factor = data.get("factor", 1)
        interval_start = datetime.strptime(data["first"], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
        interval_values = data["values"]
        interval_duration = data["interval"]

        for i, value in enumerate(interval_values):
            if value is None:
                continue
            timestamp = interval_start + pd.Timedelta(seconds=i * interval_duration)
            # Check if the timestamp falls within our desired one-month range
            if start_date <= timestamp <= end_date:
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
    relay_count = 0  # Counter for relays with data
    print("Extracting bandwidth data...")

    for relay in all_bandwidth_data:
        data_points = extract_bandwidth_data(relay)
        if data_points:
            relay_count += 1  # Increment if relay has data
        all_data_points.extend(data_points)

    # Create DataFrame
    data = pd.DataFrame(all_data_points)

    if data.empty:
        print("No data points were collected.")
        return

    # Remove timezone info
    data['Timestamp'] = pd.to_datetime(data['Timestamp']).dt.tz_localize(None)

    # Filter out relays with zero mean bandwidth to avoid division by zero
    cov_df = data.groupby('Fingerprint')['Bandwidth (B/s)'].apply(
        lambda x: x.std() / x.mean() if x.mean() != 0 else None
    ).dropna().reset_index()
    cov_df.columns = ['Fingerprint', 'Coefficient of Variation']

    # Merge CoV data with the original data points
    data = pd.merge(data, cov_df, on='Fingerprint', how='left')

    # Save to CSV with CoV included
    print("Saving data to CSV...")
    data.to_csv('relay_bandwidth_data_with_cov.csv', index=False)
    print(f"Data collection completed and saved to 'relay_bandwidth_data_with_cov.csv'.")
    print(f"Total relays with data: {relay_count}")


if __name__ == '__main__':
    main()
