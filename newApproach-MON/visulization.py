import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def plot_coefficient_variation():
    # Load data with CoV from CSV
    data = pd.read_csv('relay_bandwidth_data_with_cov.csv')

    # Drop duplicate entries to get unique CoV per relay
    coefficient_variations = data[['Fingerprint', 'Coefficient of Variation']].drop_duplicates()

     # Scatter plot
    '''plt.figure(figsize=(10, 6))
    plt.scatter(coefficient_variations['Fingerprint'], coefficient_variations['Coefficient of Variation'], alpha=0.5)
    plt.xlabel("Relay Fingerprint")
    plt.ylabel("Coefficient of Variation")
    plt.title("Coefficient of Variation for Bandwidth by Relay")
    plt.xticks(rotation=90)
    plt.show()'''

    # CDF plot
    sorted_variations = np.sort(coefficient_variations['Coefficient of Variation'])
    cdf = np.arange(len(sorted_variations)) / float(len(sorted_variations))
    plt.figure(figsize=(10, 6))
    plt.plot(sorted_variations, cdf, marker='.', linestyle='none')
    plt.xlabel("Coefficient of Variation")
    plt.ylabel("CDF")
    plt.title("CDF of Coefficient of Variation for Relay Bandwidths Monthly Reported (8/29/2024 - 9/29/2024)")
    plt.show()

if __name__ == "__main__":
    plot_coefficient_variation()
