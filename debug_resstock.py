"""Debug script to see what's failing in ResStock processing"""
import pandas as pd
import requests

url = "https://oedi-data-lake.s3.amazonaws.com/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2025/resstock_amy2018_release_1/metadata_and_annual_results/national/full/parquet/upgrade0.parquet"

print("Downloading sample...")
response = requests.get(url, stream=True, timeout=60)
temp = 'data/t.parquet'
with open(temp, 'wb') as f:
    for chunk in response.iter_content(8192):
        f.write(chunk)

df = pd.read_parquet(temp)
print(f"Downloaded {len(df)} rows")

# Sample first 100 rows
sample = df.head(100)

errors = []
for idx, row in sample.iterrows():
    try:
        # Try the conversion
        sqft = row.get('in.sqft..ft2')
        if pd.isna(sqft) or sqft == 0:
            sqft = 1500
        sqft = int(float(sqft))
        
        bedrooms = int(float(row.get('in.bedrooms', 3)))
        occupants = int(float(row.get('in.occupants', 2)))
        bldg_id = int(row.get('bldg_id', idx + 1))
        lat = float(row.get('in.weather_file_latitude', 39.8))
        lon = float(row.get('in.weather_file_longitude', -98.5))
        
    except Exception as e:
        errors.append((idx, str(e), {
            'sqft': row.get('in.sqft..ft2'),
            'bedrooms': row.get('in.bedrooms'),
            'occupants': row.get('in.occupants'),
            'bldg_id': row.get('bldg_id'),
            'lat': row.get('in.weather_file_latitude'),
            'lon': row.get('in.weather_file_longitude')
        }))

print(f"\n{len(sample) - len(errors)} succeeded, {len(errors)} failed")
if errors:
    print(f"\nFirst 5 errors:")
    for idx, err, data in errors[:5]:
        print(f"\nRow {idx}: {err}")
        print(f"  Data: {data}")

import os
os.remove(temp)
