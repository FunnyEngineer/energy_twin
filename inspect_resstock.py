"""Quick script to inspect ResStock data structure"""
import pandas as pd
import requests
import os

url = "https://oedi-data-lake.s3.amazonaws.com/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2025/resstock_amy2018_release_1/metadata_and_annual_results/national/full/parquet/upgrade0.parquet"

print("Downloading ResStock data sample...")
response = requests.get(url, stream=True, timeout=60)

if response.status_code == 200:
    temp_file = 'data/temp_inspect.parquet'
    os.makedirs('data', exist_ok=True)
    
    with open(temp_file, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    df = pd.read_parquet(temp_file)
    print(f"\n✅ Downloaded {len(df):,} buildings")
    print(f"\nTotal columns: {len(df.columns)}")
    print(f"\nFirst 30 column names:")
    for i, col in enumerate(df.columns[:30]):
        print(f"  {i+1}. {col}")
    
    print(f"\n\nSample row (first 15 columns):")
    print(df.iloc[0].head(15))
    
    print(f"\n\nLooking for key columns...")
    key_patterns = ['building_id', 'county', 'state', 'latitude', 'longitude', 'sqft', 
                    'bedrooms', 'occupants', 'geometry', 'heating', 'cooling', 'pv', 
                    'electricity', 'climate', 'weather']
    
    for pattern in key_patterns:
        matching = [col for col in df.columns if pattern.lower() in col.lower()]
        if matching:
            print(f"\n{pattern}: {matching[:5]}")
    
    os.remove(temp_file)
    print("\n\n✅ Inspection complete")
else:
    print(f"Failed to download: HTTP {response.status_code}")
