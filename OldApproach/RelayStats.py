import os
import requests
import sys
from datetime import datetime, timedelta, timezone
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import openpyxl
from io import BytesIO
from statsmodels.tsa.stattools import acf, pacf
from scipy.stats import iqr

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

            # Calculate the appropriate number of lags
            nlags = min(len(d) // 2, 40)

            # Calculate the frequency of outliers
            q75, q25 = np.percentile(d['Bandwidth (B/s)'], [75, 25])
            iqr_value = q75 - q25
            lower_bound = q25 - 1.5 * iqr_value
            upper_bound = q75 + 1.5 * iqr_value
            outliers = d[(d['Bandwidth (B/s)'] < lower_bound) | (d['Bandwidth (B/s)'] > upper_bound)]
            frequency_of_outliers = len(outliers)

            stats[dtype] = {
                'Mean (MB/s)': mean,
                'Standard Deviation (MB/s)': std_dev,
                'Range (MB/s)': bandwidth_range,
                'Coefficient of Variation': coef_of_var,
                'Median (MB/s)': np.median(d['Bandwidth (B/s)']) / (1024 * 1024),
                'IQR (MB/s)': iqr(d['Bandwidth (B/s)']) / (1024 * 1024),
                'Skewness': d['Bandwidth (B/s)'].skew(),
                'Kurtosis': d['Bandwidth (B/s)'].kurtosis(),
                'Frequency of Outliers': frequency_of_outliers,
                'ACF': acf(d['Bandwidth (B/s)'], nlags=nlags).tolist(),  # Convert to list
                'PACF': pacf(d['Bandwidth (B/s)'], nlags=nlags).tolist()  # Convert to list
            }

    return stats

def plot_bandwidth(data):
    plt.figure(figsize=(8, 4))
    
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
    plt.figure(figsize=(8, 4))
    
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
    plt.figure(figsize=(8, 4))
    
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

def plot_acf_pacf(acf_values, pacf_values, relay_name, bandwidth_type):
    plt.figure(figsize=(10, 5))
    plt.subplot(121)
    plt.stem(acf_values)
    plt.title(f'{relay_name} - {bandwidth_type} ACF')
    
    plt.subplot(122)
    plt.stem(pacf_values)
    plt.title(f'{relay_name} - {bandwidth_type} PACF')
    
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return buf

def save_statistics_to_excel(stats, data, writer, relay_name):
    # Save statistics
    stats_df = pd.DataFrame(stats).T
    stats_startrow = 1
    stats_df.to_excel(writer, sheet_name=relay_name, startrow=stats_startrow, startcol=0)

    # Save plots
    bandwidth_over_time_plot = plot_bandwidth(data)
    bandwidth_histogram_plot = plot_histogram(data)
    bandwidth_scatter_plot = plot_scatter(data)
    
    worksheet = writer.sheets[relay_name]
    
    plots_startrow = stats_startrow + len(stats_df) + 2
    img = openpyxl.drawing.image.Image(bandwidth_over_time_plot)
    worksheet.add_image(img, f'B{plots_startrow + 0}')
    
    img = openpyxl.drawing.image.Image(bandwidth_histogram_plot)
    worksheet.add_image(img, f'B{plots_startrow + 20}')
    
    img = openpyxl.drawing.image.Image(bandwidth_scatter_plot)
    worksheet.add_image(img, f'B{plots_startrow + 40}')
    
    # Save ACF and PACF plots
    acf_plot = plot_acf_pacf(stats['Total']['ACF'], stats['Total']['PACF'], relay_name, 'Total')
    worksheet.add_image(openpyxl.drawing.image.Image(acf_plot), f'B{plots_startrow + 60}')
    
    # Save data
    data_startrow = plots_startrow + 80
    data.to_excel(writer, sheet_name=relay_name, startrow=data_startrow, index=False)

def analyze_relay(fingerprint, relay_name, writer):
    try:
        # Load data
        data = load_data(fingerprint)
        
        # Calculate statistics
        stats = calculate_statistics(data)
        
        # Print statistics to console
        for dtype, stat in stats.items():
            print(f"\n{dtype} Bandwidth Statistics for {relay_name}:")
            for k, v in stat.items():
                if isinstance(v, list):
                    print(f"{k}: {v[:5]}... (list of length {len(v)})")
                else:
                    print(f"{k}: {v:.2f}")
        
        # Save statistics, data, and plots to Excel
        save_statistics_to_excel(stats, data, writer, relay_name)

    except Exception as e:
        print(f"Failed to analyze relay {relay_name} with fingerprint {fingerprint}: {e}")

def create_summary_sheet(writer, all_stats):
    if not all_stats:
        return

    # Create the Summary sheet
    writer.book.create_sheet('Summary')
    
    mean_values = []
    stddev_values = []
    median_values = []
    iqr_values = []
    skewness_values = []
    kurtosis_values = []
    coef_var_values = []
    freq_outliers_values = []
    relay_names = []

    for relay_name, stats in all_stats.items():
        try:
            mean_values.append(stats['Total']['Mean (MB/s)'])
            stddev_values.append(stats['Total']['Standard Deviation (MB/s)'])
            median_values.append(stats['Total']['Median (MB/s)'])
            iqr_values.append(stats['Total']['IQR (MB/s)'])
            skewness_values.append(stats['Total']['Skewness'])
            kurtosis_values.append(stats['Total']['Kurtosis'])
            coef_var_values.append(stats['Total']['Coefficient of Variation'])
            freq_outliers_values.append(stats['Total']['Frequency of Outliers'])
            relay_names.append(relay_name)
        except KeyError as e:
            print(f"KeyError: {e} in relay {relay_name}")

    summary_stats_df = pd.DataFrame({
        'Relay': relay_names,
        'Mean (MB/s)': mean_values,
        'Standard Deviation (MB/s)': stddev_values,
        'Median (MB/s)': median_values,
        'IQR (MB/s)': iqr_values,
        'Skewness': skewness_values,
        'Kurtosis': kurtosis_values,
        'Coefficient of Variation': coef_var_values,
        'Frequency of Outliers': freq_outliers_values
    })
    summary_stats_df.to_excel(writer, sheet_name='Summary', startrow=1, index=False)

    # Plot and save graphs for each statistic
    plot_statistics(writer, summary_stats_df, 'Mean (MB/s)', 'Mean Bandwidth for Each Relay', 'B15')
    plot_statistics(writer, summary_stats_df, 'Standard Deviation (MB/s)', 'Standard Deviation of Bandwidth for Each Relay', 'B45')
    plot_statistics(writer, summary_stats_df, 'Median (MB/s)', 'Median Bandwidth for Each Relay', 'B75')
    plot_statistics(writer, summary_stats_df, 'IQR (MB/s)', 'IQR of Bandwidth for Each Relay', 'B105')
    plot_statistics(writer, summary_stats_df, 'Skewness', 'Skewness of Bandwidth for Each Relay', 'B135')
    plot_statistics(writer, summary_stats_df, 'Kurtosis', 'Kurtosis of Bandwidth for Each Relay', 'B165')
    plot_statistics(writer, summary_stats_df, 'Coefficient of Variation', 'Coefficient of Variation for Each Relay', 'B195')
    plot_statistics(writer, summary_stats_df, 'Frequency of Outliers', 'Frequency of Outliers for Each Relay', 'B225')

def plot_statistics(writer, summary_stats_df, column, title, position):
    plt.figure(figsize=(10, 6))
    plt.bar(summary_stats_df['Relay'], summary_stats_df[column])
    plt.title(title)
    plt.xlabel('Relay')
    plt.ylabel(column)
    plt.xticks(rotation=90)
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)

    worksheet = writer.sheets['Summary']
    img = openpyxl.drawing.image.Image(buf)
    worksheet.add_image(img, position)

def main():
    if len(sys.argv) != 2:
        print("Usage: python analyze_bandwidth.py <input_excel_filename>")
        sys.exit(1)
    
    input_excel_filename = sys.argv[1]
    output_excel_filename = "Relays_Analysis.xlsx"
    
    relays_df = pd.read_excel(input_excel_filename)
    all_stats = {}

    with pd.ExcelWriter(output_excel_filename, engine='openpyxl') as writer:
        # Create a dummy sheet to ensure at least one sheet is present
        writer.book.create_sheet("DummySheet")
        
        for _, row in relays_df.iterrows():
            fingerprint = row['Fingerprint']
            relay_name = row['Relay Name']
            print(f"\nAnalyzing {relay_name} with fingerprint {fingerprint}...\n")
            try:
                analyze_relay(fingerprint, relay_name, writer)
                data = load_data(fingerprint)
                stats = calculate_statistics(data)
                all_stats[relay_name] = stats
            except Exception as e:
                print(f"Error processing relay {relay_name} with fingerprint {fingerprint}: {e}")
        
        create_summary_sheet(writer, all_stats)
        
        # Remove the dummy sheet
        del writer.book["DummySheet"]

if __name__ == "__main__":
    main()
