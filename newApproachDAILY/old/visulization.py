#visualize.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def plot_cdf():
    # Load CoV data
    data = pd.read_csv('relay_bandwidth_cov.csv')

    # Drop rows with missing CoV values
    data = data.dropna(subset=['Coefficient of Variation'])

    # Calculate and plot CDF
    sorted_cov = np.sort(data['Coefficient of Variation'].values)
    cdf = np.arange(len(sorted_cov)) / float(len(sorted_cov))
    
    plt.figure(figsize=(10, 6))
    plt.plot(sorted_cov, cdf, marker='.', linestyle='none')
    plt.xlabel("Coefficient of Variation")
    plt.ylabel("CDF")
    plt.title("CDF of Coefficient of Variation for Relay Bandwidths w/ Daily Readings 8/29 - 9/29")
    plt.show()

if __name__ == "__main__":
    plot_cdf()
