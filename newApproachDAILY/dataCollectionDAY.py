import requests
from datetime import datetime, timezone, timedelta
import pandas as pd
import time

def fetch_daily_bandwidth_data(date):
    """Fetch bandwidth data for all relays for a specific date range."""
    limit = 5000  # Max allowed by the Onionoo API
    all_bandwidth_data = []
    start_date = date.strftime('%Y-%m-%d')
    end_date = (date + timedelta(days=1)).strftime('%Y-%m-%d')  # Next day for 24-hour window
    
    offset = 0
    while True:
        url = f'https://onionoo.torproject.org/bandwidth?type=relay&limit={limit}&offset={offset}&start={start_date}&end={end_date}'
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            raise Exception(f"Failed to fetch bandwidth data for date {start_date}")

        data = response.json()
        relays = data.get('relays', [])
        if not relays:
            break
        all_bandwidth_data.extend(relays)
        
        if len(relays) < limit:
            break
        offset += limit
        time.sleep(1)  # Avoid overloading the server

    return all_bandwidth_data

def extract_bandwidth_data(relay, start_date, end_date):
    """Extract bandwidth data points for a relay within the date range."""
    fingerprint = relay.get('fingerprint')
    write_history = relay.get('write_history')
    read_history = relay.get('read_history')
    if not write_history and not read_history:
        return []

    data_points = []
    
    # For both write and read histories
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
            timestamp = interval_start + timedelta(seconds=i * interval_duration)
            # Filter within the specific day range
            if start_date <= timestamp < end_date:
                data_points.append({
                    'Fingerprint': fingerprint,
                    'Timestamp': timestamp,
                    'Type': data_type,
                    'Bandwidth (B/s)': value * interval_factor
                })

    return data_points

def main():
    print("Fetching bandwidth data for each day over the last month...")
    all_data_points = []
    end_date = datetime.now(timezone.utc) - timedelta(days=30)  # One month ago from today

    for days_ago in range(30):
        specific_date = datetime.now(timezone.utc) - timedelta(days=days_ago + 1)
        print(f"Fetching data for {specific_date.strftime('%Y-%m-%d')}...")
        
        # Fetch data for the specific date
        daily_bandwidth_data = fetch_daily_bandwidth_data(specific_date)
        for relay in daily_bandwidth_data:
            # Extract data points for the specific date
            data_points = extract_bandwidth_data(relay, specific_date, specific_date + timedelta(days=1))
            all_data_points.extend(data_points)

    # Create DataFrame
    data = pd.DataFrame(all_data_points)

    if data.empty:
        print("No data points were collected.")
        return

    # Remove timezone info for consistency
    data['Timestamp'] = pd.to_datetime(data['Timestamp']).dt.tz_localize(None)

    # Calculate CoV for each relay
    cov_df = data.groupby('Fingerprint')['Bandwidth (B/s)'].apply(
        lambda x: x.std() / x.mean() if x.mean() != 0 else None
    ).dropna().reset_index()
    cov_df.columns = ['Fingerprint', 'Coefficient of Variation']

    # Merge CoV data with the original data points
    data = pd.merge(data, cov_df, on='Fingerprint', how='left')

    # Save to CSV with CoV included
    print("Saving data to CSV...")
    data.to_csv('relay_bandwidth_data_with_cov.csv', index=False)
    print("Data collection completed and saved to 'relay_bandwidth_data_with_cov.csv'.")

if __name__ == '__main__':
    main()
