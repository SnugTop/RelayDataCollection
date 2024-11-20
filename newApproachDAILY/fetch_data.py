# fetch_data.py
import requests
from datetime import datetime, timezone, timedelta
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def fetch_bandwidth_history(fingerprint, session):
    url = f"https://onionoo.torproject.org/bandwidth?lookup={fingerprint}"
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {fingerprint}: {e}")
        return None

    bandwidth_data = response.json()
    if not bandwidth_data.get("relays"):
        print(f"Warning: No relay data found for {fingerprint}")
        return None

    relay_info = bandwidth_data["relays"][0]
    return relay_info.get("write_history"), relay_info.get("read_history")

def extract_daily_bandwidth_data(history, start_date, end_date, direction, fingerprint):
    data_points = []
    for data in history.values():
        interval_factor = data.get("factor", 1)
        interval_start = datetime.strptime(data["first"], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
        interval_values = data["values"]
        interval_duration = data["interval"]

        for i, value in enumerate(interval_values):
            if value is None:
                continue
            timestamp = interval_start + timedelta(seconds=i * interval_duration)
            if start_date <= timestamp < end_date:
                data_points.append({
                    "Fingerprint": fingerprint,
                    "Timestamp": timestamp.isoformat(),
                    "Direction": direction,
                    "Value": value * interval_factor
                })
    return data_points

def process_relay(fingerprint, cutoff_start, cutoff_end, session):
    print(f"Starting processing for relay {fingerprint}...")
    result = fetch_bandwidth_history(fingerprint, session)
    if result is None:
        print(f"No bandwidth history found for {fingerprint}. Skipping.")
        return []

    write_history, read_history = result
    write_data = extract_daily_bandwidth_data(write_history, cutoff_start, cutoff_end, "Write", fingerprint) if write_history else []
    read_data = extract_daily_bandwidth_data(read_history, cutoff_start, cutoff_end, "Read", fingerprint) if read_history else []
    combined_data = write_data + read_data

    print(f"Completed processing for relay {fingerprint}.")
    return combined_data

def fetch_bandwidth_data_concurrent(fingerprints, months_ago=2, month_duration=1):
    cutoff_start = datetime.now(timezone.utc) - timedelta(days=months_ago * 30)
    cutoff_end = cutoff_start + timedelta(days=month_duration * 30)
    all_data = []
    total_relays = len(fingerprints)

    # Configure retries for the session
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504], allowed_methods=["GET"])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('https://', adapter)

    max_workers = 5  # Reduce the number of concurrent threads
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_relay, fp, cutoff_start, cutoff_end, session): fp
            for fp in fingerprints
        }
        for i, future in enumerate(as_completed(futures), start=1):
            try:
                result = future.result()
                if result:
                    all_data.extend(result)
                print(f"Processed {i}/{total_relays} relays.")
            except Exception as e:
                print(f"Error processing relay {futures[future]}: {e}")

    session.close()
    return all_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fetch bandwidth data for relays.')
    parser.add_argument('input_csv', help='Input CSV file containing relay fingerprints.')
    args = parser.parse_args()

    fingerprints_df = pd.read_csv(args.input_csv)
    fingerprints = fingerprints_df['Fingerprint'].tolist()

    bandwidth_data = fetch_bandwidth_data_concurrent(fingerprints)
    if bandwidth_data:
        df = pd.DataFrame(bandwidth_data)
        df.to_csv('relay_bandwidth_data.csv', index=False)
        print("Saved bandwidth data to 'relay_bandwidth_data.csv'.")
    else:
        print("No bandwidth data collected.")
