# visualize.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse

def plot_cdf(data, column, xlabel, title, x_units=None, x_limit=None, x_ticks=None, hline_y=None):
    # Drop rows with missing values
    data = data.dropna(subset=[column])

    # Calculate and plot CDF
    sorted_data = np.sort(data[column].values)
    cdf = np.arange(1, len(sorted_data) + 1) / float(len(sorted_data))

    plt.figure(figsize=(10, 6))
    plt.plot(sorted_data, cdf, marker='.', linestyle='none')

    # Add units to xlabel if provided
    if x_units:
        plt.xlabel(f"{xlabel} ({x_units})")
    else:
        plt.xlabel(xlabel)

    plt.ylabel("CDF")
    plt.title(title)
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)

    # Set x-axis limit if provided
    if x_limit is not None:
        plt.xlim(x_limit)

    # Set x-axis ticks if provided
    if x_ticks is not None:
        plt.xticks(x_ticks)

    # Add horizontal line at specified y-value
    if hline_y is not None:
        plt.axhline(y=hline_y, color='red', linestyle='--', label=f'y = {hline_y}')
        plt.legend()

    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Visualize relay bandwidth statistics.')
    parser.add_argument('input_csv', help='Input CSV file containing statistics data.')
    args = parser.parse_args()

    # Load statistics data
    data = pd.read_csv(args.input_csv)

    # Plot CDF of Coefficient of Variation with styling changes
    # Limit x-axis to 0 - 2 and set x-axis ticks at regular intervals
    x_limit_cov = [0, 2]
    x_ticks_cov = np.arange(0, 2.1, 0.2)  # Ticks every 0.2 units from 0 to 2

    plot_cdf(
        data,
        'Coefficient of Variation',
        'Coefficient of Variation',
        'CDF of Coefficient of Variation for Relay Bandwidths',
        x_units='Unitless',
        x_limit=x_limit_cov,
        x_ticks=x_ticks_cov,
        hline_y=0.5  # Add horizontal line at y=0.5
    )

    # Plot CDF of Standard Deviation with units and grid lines
    # Adjust x-axis ticks for clarity
    std_data = data['Standard Deviation'].dropna()
    std_max = std_data.max()
    x_limit_std = [0, std_max]
    x_ticks_std = np.linspace(0, std_max, num=10)  # 10 ticks from 0 to max

    plot_cdf(
        data,
        'Standard Deviation',
        'Standard Deviation',
        'CDF of Standard Deviation for Relay Bandwidths',
        x_units='Bytes/sec',
        x_limit=x_limit_std,
        x_ticks=x_ticks_std
    )
