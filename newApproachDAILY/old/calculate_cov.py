#calculate_cov.py
import requests
from datetime import datetime, timezone, timedelta
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_bandwidth_history(fingerprint):
    url = f"https://onionoo.torproject.org/bandwidth?lookup={fingerprint}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error fetching {fingerprint}: {response.status_code} - {response.text}")
        return None

    bandwidth_data = response.json()
    if not bandwidth_data.get("relays"):
        print(f"Warning: No relay data found for {fingerprint}")
        return None

    relay_info = bandwidth_data["relays"][0]
    return relay_info.get("write_history"), relay_info.get("read_history")

def extract_daily_bandwidth_data(history, start_date, end_date):
    data_points = []
    for interval, data in history.items():
        interval_factor = data.get("factor", 1)
        interval_start = datetime.strptime(data["first"], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
        interval_values = data["values"]
        interval_duration = data["interval"]

        for i, value in enumerate(interval_values):
            if value is None:
                continue
            timestamp = interval_start + timedelta(seconds=i * interval_duration)
            if start_date <= timestamp < end_date:
                data_points.append(value * interval_factor)
    return data_points

def process_relay(fingerprint, cutoff_start, cutoff_end):
    print(f"Starting processing for relay {fingerprint}...")
    result = fetch_bandwidth_history(fingerprint)
    if result is None:
        print(f"No bandwidth history found for {fingerprint}. Skipping.")
        return None
    
    write_history, read_history = result
    write_data = extract_daily_bandwidth_data(write_history, cutoff_start, cutoff_end) if write_history else []
    read_data = extract_daily_bandwidth_data(read_history, cutoff_start, cutoff_end) if read_history else []
    combined_data = write_data + read_data

    if combined_data:
        cov = (pd.Series(combined_data).std() / pd.Series(combined_data).mean()) if pd.Series(combined_data).mean() != 0 else None
        print(f"Completed processing for relay {fingerprint}. CoV: {cov}")
        return {"Fingerprint": fingerprint, "Coefficient of Variation": cov}


def calculate_cov_concurrent(fingerprints, months_ago=2, month_duration=1):
    cutoff_start = datetime.now(timezone.utc) - timedelta(days=months_ago * 30)
    cutoff_end = cutoff_start + timedelta(days=month_duration * 30)
    all_data = []
    total_relays = len(fingerprints)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_relay, fp, cutoff_start, cutoff_end): fp for fp in fingerprints}
        for i, future in enumerate(as_completed(futures), start=1):
            result = future.result()
            if result:
                all_data.append(result)
            print(f"Processed {i}/{total_relays} relays.")

    return pd.DataFrame(all_data)

if __name__ == "__main__":
    fingerprints_df = pd.read_csv('relay_fingerprints.csv')
    fingerprints = fingerprints_df['Fingerprint'].tolist()
    
    cov_data = calculate_cov_concurrent(fingerprints)
    cov_data.to_csv('relay_bandwidth_cov.csv', index=False)
    print("Saved CoV data to 'relay_bandwidth_cov.csv'.")
