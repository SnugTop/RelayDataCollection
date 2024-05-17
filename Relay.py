import os
import requests
import sys
from datetime import datetime, timedelta, timezone
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import openpyxl
from io import BytesIO

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

def load_data(fingerprint, months=6):
    write_history, read_history = fetch_bandwidth_history(fingerprint)

    recent_write_history = extract_recent_bandwidth(write_history, months)
    recent_read_history = extract_recent_bandwidth(read_history, months)

    combined_history = [(timestamp, "Write", bandwidth) for timestamp, bandwidth in recent_write_history] + \
                       [(timestamp, "Read", bandwidth) for timestamp, bandwidth in recent_read_history]

    combined_history.sort(key=lambda x: x[0])  # Sort by timestamp

    if not combined_history:
        print("No bandwidth data available for the specified period.")
        return pd.DataFrame(columns=["Timestamp", "Type", "Bandwidth (B/s)"])

    data = pd.DataFrame(combined_history, columns=["Timestamp", "Type", "Bandwidth (B/s)"])
    data['Timestamp'] = pd.to_datetime(data['Timestamp']).dt.tz_localize(None)  # Make timezone-unaware
    return data

def calculate_statistics(data):
    stats = {}
    
    # Separate read and write data
    read_data = data[data['Type'] == 'Read']
    write_data = data[data['Type'] == 'Write']
    
    # Calculate stats for read, write, and total bandwidths
    for dtype, d in [('Read', read_data), ('Write', write_data), ('Total', data)]:
        if not d.empty:
            mean = d['Bandwidth (B/s)'].mean() / (1024 * 1024)  # Convert to MB/s
            std_dev = d['Bandwidth (B/s)'].std() / (1024 * 1024)  # Convert to MB/s
            bandwidth_range = (d['Bandwidth (B/s)'].max() - d['Bandwidth (B/s)'].min()) / (1024 * 1024)  # Convert to MB/s
            coef_of_var = std_dev / mean if mean != 0 else np.nan

            stats[dtype] = {
                'Mean (MB/s)': mean,
                'Standard Deviation (MB/s)': std_dev,
                'Range (MB/s)': bandwidth_range,
                'Coefficient of Variation': coef_of_var
            }

    return stats

def plot_bandwidth(data):
    plt.figure(figsize=(12, 6))
    
    for dtype in ['Read', 'Write']:
        d = data[data['Type'] == dtype]
        if not d.empty:
            plt.plot(d['Timestamp'], d['Bandwidth (B/s)'] / (1024 * 1024), label=f'{dtype} Bandwidth')

    plt.xlabel('Timestamp')
    plt.ylabel('Bandwidth (MB/s)')
    plt.title('Bandwidth Over Time')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return buf

def plot_histogram(data):
    plt.figure(figsize=(12, 6))
    
    for dtype in ['Read', 'Write']:
        d = data[data['Type'] == dtype]
        if not d.empty:
            plt.hist(d['Bandwidth (B/s)'] / (1024 * 1024), bins=50, alpha=0.5, label=f'{dtype} Bandwidth')

    plt.xlabel('Bandwidth (MB/s)')
    plt.ylabel('Frequency')
    plt.title('Histogram of Bandwidth Fluctuations')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return buf

def plot_scatter(data):
    plt.figure(figsize=(12, 6))
    
    read_data = data[data['Type'] == 'Read']
    write_data = data[data['Type'] == 'Write']
    
    plt.scatter(read_data['Timestamp'], read_data['Bandwidth (B/s)'] / (1024 * 1024), alpha=0.5, label='Read Bandwidth')
    plt.scatter(write_data['Timestamp'], write_data['Bandwidth (B/s)'] / (1024 * 1024), alpha=0.5, label='Write Bandwidth')
    
    plt.xlabel('Timestamp')
    plt.ylabel('Bandwidth (MB/s)')
    plt.title('Scatter Plot of Read and Write Bandwidths Over Time')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return buf

def plot_boxplot(data):
    plt.figure(figsize=(12, 6))
    
    read_data = data[data['Type'] == 'Read']['Bandwidth (B/s)'] / (1024 * 1024)
    write_data = data[data['Type'] == 'Write']['Bandwidth (B/s)'] / (1024 * 1024)
    
    plt.boxplot([read_data, write_data], labels=['Read', 'Write'])
    
    plt.ylabel('Bandwidth (MB/s)')
    plt.title('Box Plot of Read and Write Bandwidths')
    plt.grid(True)
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return buf

def save_statistics_to_excel(stats, data, excel_filename):
    with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
        # Save statistics
        stats_df = pd.DataFrame(stats).T
        stats_df.to_excel(writer, sheet_name='Statistics')
        
        # Save data
        data.to_excel(writer, sheet_name='Data', index=False)
        
        # Save plots
        bandwidth_over_time_plot = plot_bandwidth(data)
        bandwidth_histogram_plot = plot_histogram(data)
        bandwidth_scatter_plot = plot_scatter(data)
        bandwidth_boxplot_plot = plot_boxplot(data)
        
        worksheet = writer.book.create_sheet('Plots')
        worksheet = writer.sheets['Plots']
        
        img = openpyxl.drawing.image.Image(bandwidth_over_time_plot)
        worksheet.add_image(img, 'A1')
        
        img = openpyxl.drawing.image.Image(bandwidth_histogram_plot)
        worksheet.add_image(img, 'A30')
        
        img = openpyxl.drawing.image.Image(bandwidth_scatter_plot)
        worksheet.add_image(img, 'A60')
        
        img = openpyxl.drawing.image.Image(bandwidth_boxplot_plot)
        worksheet.add_image(img, 'A90')

def analyze_relay(fingerprint, relay_name, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    excel_filename = os.path.join(output_dir, f"{relay_name}.xlsx")
    
    try:
        # Load data
        data = load_data(fingerprint)
        
        # Calculate statistics
        stats = calculate_statistics(data)
        
        # Print statistics to console
        for dtype, stat in stats.items():
            print(f"\n{dtype} Bandwidth Statistics for {relay_name}:")
            for k, v in stat.items():
                print(f"{k}: {v:.2f}")
        
        # Save statistics, data, and plots to Excel
        save_statistics_to_excel(stats, data, excel_filename)

    except Exception as e:
        print(f"Failed to analyze relay {relay_name} with fingerprint {fingerprint}: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python analyze_bandwidth.py <input_excel_filename>")
        sys.exit(1)
    
    input_excel_filename = sys.argv[1]
    output_dir = "Files"
    
    relays_df = pd.read_excel(input_excel_filename)
    
    for _, row in relays_df.iterrows():
        fingerprint = row['Fingerprint']
        relay_name = row['Relay Name']
        print(f"\nAnalyzing {relay_name} with fingerprint {fingerprint}...\n")
        analyze_relay(fingerprint, relay_name, output_dir)

if __name__ == "__main__":
    main()
