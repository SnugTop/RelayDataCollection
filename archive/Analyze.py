import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import openpyxl

def load_data(csv_filename):
    data = pd.read_csv(csv_filename, parse_dates=['Timestamp'])
    data['Bandwidth (B/s)'] = data['Bandwidth (B/s)'].astype(float)
    return data

def calculate_statistics(data):
    stats = {}
    
    # Separate read and write data
    read_data = data[data['Type'] == 'Read']
    write_data = data[data['Type'] == 'Write']
    
    # Calculate stats for read, write, and total bandwidths
    for dtype, d in [('Read', read_data), ('Write', write_data), ('Total', data)]:
        if not d.empty:
            mean = d['Bandwidth (B/s)'].mean()
            std_dev = d['Bandwidth (B/s)'].std()
            bandwidth_range = d['Bandwidth (B/s)'].max() - d['Bandwidth (B/s)'].min()
            coef_of_var = std_dev / mean if mean != 0 else np.nan

            stats[dtype] = {
                'Mean': mean,
                'Standard Deviation': std_dev,
                'Range': bandwidth_range,
                'Coefficient of Variation': coef_of_var
            }

    return stats

def plot_bandwidth(data):
    plt.figure(figsize=(12, 6))
    
    for dtype in ['Read', 'Write']:
        d = data[data['Type'] == dtype]
        if not d.empty:
            plt.plot(d['Timestamp'], d['Bandwidth (B/s)'], label=f'{dtype} Bandwidth')

    plt.xlabel('Timestamp')
    plt.ylabel('Bandwidth (B/s)')
    plt.title('Bandwidth Over Time')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('bandwidth_over_time.png')
    plt.close()

def plot_histogram(data):
    plt.figure(figsize=(12, 6))
    
    for dtype in ['Read', 'Write']:
        d = data[data['Type'] == dtype]
        if not d.empty:
            plt.hist(d['Bandwidth (B/s)'], bins=50, alpha=0.5, label=f'{dtype} Bandwidth')

    plt.xlabel('Bandwidth (B/s)')
    plt.ylabel('Frequency')
    plt.title('Histogram of Bandwidth Fluctuations')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('bandwidth_histogram.png')
    plt.close()

def save_statistics_to_excel(stats, data, excel_filename):
    with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
        # Save statistics
        stats_df = pd.DataFrame(stats).T
        stats_df.to_excel(writer, sheet_name='Statistics')
        
        # Save data
        data.to_excel(writer, sheet_name='Data', index=False)
        
        # Save plots
        bandwidth_over_time_plot = 'bandwidth_over_time.png'
        bandwidth_histogram_plot = 'bandwidth_histogram.png'
        
        worksheet = writer.book.create_sheet('Plots')
        worksheet = writer.sheets['Plots']
        
        img = openpyxl.drawing.image.Image(bandwidth_over_time_plot)
        worksheet.add_image(img, 'A1')
        
        img = openpyxl.drawing.image.Image(bandwidth_histogram_plot)
        worksheet.add_image(img, 'A30')

def main():
    if len(sys.argv) != 2:
        print("Usage: python analyze_bandwidth.py <input_csv_filename>")
        sys.exit(1)
    
    csv_filename = sys.argv[1]
    excel_filename = csv_filename.replace('.csv', '.xlsx')
    
    data = load_data(csv_filename)
    
    # Calculate statistics
    stats = calculate_statistics(data)
    
    # Print statistics to console
    for dtype, stat in stats.items():
        print(f"\n{dtype} Bandwidth Statistics:")
        for k, v in stat.items():
            print(f"{k}: {v:.2f}")
    
    # Plot bandwidth over time
    plot_bandwidth(data)
    
    # Plot histogram of bandwidth fluctuations
    plot_histogram(data)
    
    # Save statistics, data, and plots to Excel
    save_statistics_to_excel(stats, data, excel_filename)

if __name__ == "__main__":
    main()
