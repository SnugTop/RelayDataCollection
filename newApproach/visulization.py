import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def calculate_coefficient_of_variation(df):
    relay_groups = df.groupby('Fingerprint')['Bandwidth (B/s)']
    coefficient_variations = relay_groups.std() / relay_groups.mean()
    return coefficient_variations.dropna()

def plot_coefficient_variation(coefficient_variations):
    # Scatter plot
    plt.figure(figsize=(10, 6))
    plt.scatter(coefficient_variations.index, coefficient_variations.values, alpha=0.5)
    plt.xlabel("Relay Fingerprint")
    plt.ylabel("Coefficient of Variation")
    plt.title("Coefficient of Variation for Bandwidth by Relay")
    plt.xticks(rotation=90)
    plt.show()

    # CDF plot
    sorted_variations = np.sort(coefficient_variations.values)
    cdf = np.arange(len(sorted_variations)) / float(len(sorted_variations))
    plt.figure(figsize=(10, 6))
    plt.plot(sorted_variations, cdf, marker='.', linestyle='none')
    plt.xlabel("Coefficient of Variation")
    plt.ylabel("CDF")
    plt.title("CDF of Coefficient of Variation for Relay Bandwidths")
    plt.show()

def main():
    # Load data from CSV
    df = pd.read_csv('relay_bandwidth_data.csv')

    # Calculate coefficient of variation for each relay
    coefficient_variations = calculate_coefficient_of_variation(df)

    # Plot the results
    plot_coefficient_variation(coefficient_variations)

if __name__ == "__main__":
    main()
