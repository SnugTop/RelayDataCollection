import requests
import csv
import sys
from datetime import datetime, timedelta, timezone

def fetch_bandwidth_history(fingerprint):
    url = f"https://onionoo.torproject.org/bandwidth?lookup={fingerprint}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        raise Exception(f"Failed to fetch bandwidth data for relay {fingerprint}")

    bandwidth_data = response.json()
    if not bandwidth_data.get("relays"):
        raise Exception(f"No bandwidth data found for relay {fingerprint}")

    relay_info = bandwidth_data["relays"][0]
    return relay_info.get("write_history"), relay_info.get("read_history")

def extract_recent_bandwidth(history, months=6):
    cutoff = datetime.now(timezone.utc) - timedelta(days=months*30)
    recent_history = []

    if not history:
        return recent_history

    for interval, data in history.items():
        interval_factor = data.get("factor", 1)
        interval_start = datetime.strptime(data["first"], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
        interval_values = data["values"]
        interval_duration = data["interval"]

        for i, value in enumerate(interval_values):
            timestamp = interval_start + timedelta(seconds=i * interval_duration)
            if timestamp >= cutoff:
                recent_history.append((timestamp, value * interval_factor))

    return recent_history

def save_bandwidth_history_to_csv(fingerprint, filename, months=6):
    try:
        write_history, read_history = fetch_bandwidth_history(fingerprint)

        recent_write_history = extract_recent_bandwidth(write_history, months)
        recent_read_history = extract_recent_bandwidth(read_history, months)

        combined_history = [(timestamp, "Write", bandwidth) for timestamp, bandwidth in recent_write_history] + \
                           [(timestamp, "Read", bandwidth) for timestamp, bandwidth in recent_read_history]
        
        combined_history.sort(key=lambda x: x[0])  # Sort by timestamp

        if not combined_history:
            print("No bandwidth data available for the specified period.")
            return

        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Timestamp", "Type", "Bandwidth (B/s)"])

            for entry in combined_history:
                bandwidth_mb = entry[2]
                writer.writerow([entry[0].strftime('%Y-%m-%d %H:%M:%S'), entry[1], f"{bandwidth_mb:.2f}"])

        print(f"Bandwidth history for relay {fingerprint} saved to {filename}")

    except Exception as e:
        print(e)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python RealyOnionoo.py <relay_fingerprint> <output_csv_filename>")
        sys.exit(1)
    
    fingerprint = sys.argv[1]
    output_filename = sys.argv[2]
    save_bandwidth_history_to_csv(fingerprint, output_filename)
