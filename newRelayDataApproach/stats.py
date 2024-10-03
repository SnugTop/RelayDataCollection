import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def main():
    # Read in the CSV data
    data = pd.read_csv('relay_bandwidth_data.csv', parse_dates=['Timestamp'])

    # Filter data to September 2024 if possible
    # Adjust dates according to available data
    start_date = pd.Timestamp('2024-09-01')
    end_date = pd.Timestamp('2024-10-01')
    data = data[(data['Timestamp'] >= start_date) & (data['Timestamp'] < end_date)]

    if data.empty:
        print("No data available for September 2024. Using all available data.")
        data = pd.read_csv('relay_bandwidth_data.csv', parse_dates=['Timestamp'])

    # For each relay, calculate the coefficient of variation
    grouped = data.groupby('Fingerprint')

    coef_vars = {}

    for fingerprint, group in grouped:
        bandwidths = group['Bandwidth (B/s)']
        mean = bandwidths.mean()
        std_dev = bandwidths.std()
        coef_var = std_dev / mean if mean != 0 else np.nan
        if not np.isnan(coef_var):
            coef_vars[fingerprint] = coef_var

    # Create a DataFrame from the coefficients of variation
    coef_var_df = pd.DataFrame(list(coef_vars.items()), columns=['Fingerprint', 'Coefficient of Variation'])

    # Save the coefficients to a CSV file
    coef_var_df.to_csv('coefficients_of_variation.csv', index=False)

    # Plot the coefficient of variation histogram
    plt.figure(figsize=(10, 6))
    plt.hist(coef_var_df['Coefficient of Variation'], bins=50, color='skyblue', edgecolor='black')
    plt.xlabel('Coefficient of Variation')
    plt.ylabel('Number of Relays')
    plt.title('Histogram of Coefficient of Variation of Relay Bandwidths')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('coefficient_of_variation_histogram.png')
    plt.close()

    # Plot the CDF of the coefficient of variation
    sorted_coef_var = np.sort(coef_var_df['Coefficient of Variation'])
    cdf = np.arange(1, len(sorted_coef_var)+1) / len(sorted_coef_var)
    plt.figure(figsize=(10, 6))
    plt.plot(sorted_coef_var, cdf, marker='.', linestyle='none')
    plt.xlabel('Coefficient of Variation')
    plt.ylabel('CDF')
    plt.title('CDF of Coefficient of Variation of Relay Bandwidths')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('coefficient_of_variation_cdf.png')
    plt.close()

    print("Statistics calculated and graphs saved:")
    print("- 'coefficients_of_variation.csv'")
    print("- 'coefficient_of_variation_histogram.png'")
    print("- 'coefficient_of_variation_cdf.png'")

if __name__ == '__main__':
    main()
