import pandas as pd
import numpy as np
import datetime

# --- Configuration ---
START_DATE = '2022-01-01'
END_DATE = '2025-08-25'
BUSINESS_LINES = {
    'Commercial Auto': 0.65,
    'General Liability': 0.75,
    'Workers Compensation': 0.55,
    'Commercial Property': 0.45
}
REGIONS = ['Northeast', 'Southeast', 'Midwest', 'West']

print("Starting data generation process...")

# --- 1. Create Dimension Tables ---

# Create Date Dimension
print("Creating Date Dimension table...")
date_range = pd.to_datetime(pd.date_range(start=START_DATE, end=END_DATE, freq='D'))
dim_date = pd.DataFrame({
    'date_key': date_range.strftime('%Y%m%d').astype(int),
    'full_date': date_range,
    'year': date_range.year,
    'quarter': 'Q' + date_range.quarter.astype(str),
    'month': date_range.month,
    'month_name': date_range.strftime('%B')
})
dim_date.to_csv('dim_date.csv', index=False)
print("... `dim_date.csv` created successfully.")

# Create Business Line Dimension
print("Creating Business Line Dimension table...")
dim_business_line = pd.DataFrame({
    'business_line_key': range(1, len(BUSINESS_LINES) + 1),
    'line_name': list(BUSINESS_LINES.keys())
})
dim_business_line.to_csv('dim_business_line.csv', index=False)
print("... `dim_business_line.csv` created successfully.")

# Create Region Dimension
print("Creating Region Dimension table...")
dim_region = pd.DataFrame({
    'region_key': range(1, len(REGIONS) + 1),
    'region_name': REGIONS
})
dim_region.to_csv('dim_region.csv', index=False)
print("... `dim_region.csv` created successfully.")


# --- 2. Create Fact Table ---
print("Creating Financial Fact table...")

# Create a base DataFrame with every combination of date, business line, and region
df_keys = pd.MultiIndex.from_product([
    dim_date['date_key'],
    dim_business_line['business_line_key'],
    dim_region['region_key']
], names=['date_key', 'business_line_key', 'region_key']).to_frame(index=False)


# Generate financial data
# This part simulates realistic-looking data with trends and noise.
np.random.seed(42)
num_records = len(df_keys)

# Base premium and loss values
df_keys['earned_premium'] = np.random.uniform(5000, 15000, num_records)

# Merge with dimensions to get names for calculations
df_merged = pd.merge(df_keys, dim_business_line, on='business_line_key')
df_merged = pd.merge(df_merged, dim_date, on='date_key')

# Calculate incurred loss based on the base loss ratio for each business line
# We add some noise and seasonality for realism
base_loss_ratios = df_merged['line_name'].map(BUSINESS_LINES)
seasonal_factor = 1 + np.sin(df_merged['month'] * 2 * np.pi / 12) * 0.1 # +/- 10% seasonality
random_noise = np.random.normal(1, 0.05, num_records) # Random noise
trend_factor = 1 + (df_merged['full_date'] - df_merged['full_date'].min()).dt.days / 1000 * 0.05 # Slight upward trend

# Calculate incurred loss
df_merged['incurred_loss'] = df_merged['earned_premium'] * base_loss_ratios * seasonal_factor * random_noise * trend_factor

# Finalize the fact table
fact_financials = df_merged[['date_key', 'business_line_key', 'region_key', 'earned_premium', 'incurred_loss']]
fact_financials = fact_financials.round(2)

fact_financials.to_csv('fact_financials.csv', index=False)
print("... `fact_financials.csv` created successfully.")
print("\nData generation complete!")

