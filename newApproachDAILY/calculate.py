# calculate.py
import pandas as pd
import numpy as np
import argparse

def calculate_statistics(df):
    results = []
    grouped = df.groupby('Fingerprint')

    for fingerprint, group in grouped:
        combined_values = group['Value']
        if not combined_values.empty:
            mean = combined_values.mean()
            std = combined_values.std()
            cov = std / mean if mean != 0 else None

            result = {
                "Fingerprint": fingerprint,
                "Mean Bandwidth": mean,
                "Standard Deviation": std,
                "Coefficient of Variation": cov
            }
            results.append(result)
        else:
            print(f"No data available for relay {fingerprint}")

    return pd.DataFrame(results)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Calculate statistics for relay bandwidth data.')
    parser.add_argument('input_csv', help='Input CSV file containing bandwidth data.')
    args = parser.parse_args()

    df = pd.read_csv(args.input_csv)
    stats_df = calculate_statistics(df)
    stats_df.to_csv('relay_bandwidth_stats.csv', index=False)
    print("Saved statistics data to 'relay_bandwidth_stats.csv'.")
