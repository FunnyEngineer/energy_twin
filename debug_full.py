"""More detailed debugging"""
import pandas as pd
import requests
import os

def _map_building_type(resstock_type):
    type_str = str(resstock_type)
    if 'Single-Family Detached' in type_str or 'Mobile Home' in type_str:
        return 'house'
    elif 'Single-Family Attached' in type_str:
        return 'condo'
    elif 'Unit' in type_str or 'Multi-Family' in type_str or 'Apartment' in type_str:
        return 'apartment'
    else:
        return 'house'

def _map_heating_fuel(fuel):
    fuel_str = str(fuel).lower()
    if 'gas' in fuel_str or 'natural gas' in fuel_str:
        return 'gas'
    elif 'electric' in fuel_str or 'electricity' in fuel_str:
        return 'electric'
    elif 'oil' in fuel_str or 'fuel oil' in fuel_str:
        return 'oil'
    elif 'propane' in fuel_str:
        return 'gas'
    elif 'heat pump' in fuel_str:
        return 'heat_pump'
    else:
        return 'other'

def _map_cooling_type(cooling):
    cooling_str = str(cooling).lower()
    if 'central' in cooling_str:
        return 'central_ac'
    elif 'room' in cooling_str or 'window' in cooling_str:
        return 'window_ac'
    elif 'heat pump' in cooling_str:
        return 'heat_pump'
    elif 'none' in cooling_str or 'no' in cooling_str:
        return 'none'
    else:
        return 'central_ac'

url = "https://oedi-data-lake.s3.amazonaws.com/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2025/resstock_amy2018_release_1/metadata_and_annual_results/national/full/parquet/upgrade0.parquet"

print("Downloading...")
response = requests.get(url, stream=True, timeout=60)
temp = 'data/t.parquet'
with open(temp, 'wb') as f:
    for chunk in response.iter_content(8192):
        f.write(chunk)

df = pd.read_parquet(temp)
sample = df.head(100)

elec_cols = [col for col in df.columns if 'out.electricity.total.energy_consumption' in col and 'intensity' not in col]
total_elec_col = elec_cols[0] if elec_cols else None
print(f"Using column: {total_elec_col}")

success = 0
fail = 0
error_types = {}

for idx, row in sample.iterrows():
    try:
        # Full processing
        city = str(row.get('in.weather_file_city', row.get('in.city', 'Unknown'))).strip()
        state = str(row.get('in.state', 'USA')).strip()
        
        if 'another census' in city.lower() or 'not in a census' in city.lower():
            city = state
            
        location = f"{city}, {state}" if city and city != state else state
        
        sqft = row.get('in.sqft..ft2')
        if pd.isna(sqft) or sqft == 0:
            sqft = 1500
        sqft = int(float(sqft))
        
        monthly_usage = 900
        if total_elec_col:
            annual = row.get(total_elec_col)
            if pd.notna(annual) and annual > 0:
                monthly_usage = int(float(annual) / 12)
        
        building_type = row.get('in.geometry_building_type_acs', 
                              row.get('in.geometry_building_type_recs', 'Single-Family Detached'))
        
        bedrooms_raw = row.get('in.bedrooms', 3)
        if pd.isna(bedrooms_raw):
            bedrooms = 3
        else:
            bedrooms = int(float(str(bedrooms_raw).replace('+', '')))
        
        occupants_raw = row.get('in.occupants', 2)
        if pd.isna(occupants_raw):
            occupants = 2
        else:
            occupants_str = str(occupants_raw).replace('+', '').strip()
            occupants = int(float(occupants_str)) if occupants_str else 2
        
        heating_fuel = str(row.get('in.heating_fuel', 'Natural Gas'))
        
        cooling = row.get('in.hvac_cooling_efficiency', 
                        row.get('in.hvac_cooling_type', 
                               row.get('in.cooling_setpoint', 'Central AC')))
        
        has_pv = row.get('in.has_pv', 'No')
        pv_size = row.get('in.pv_system_size', 0)
        has_solar = (str(has_pv).lower() == 'yes' or (pd.notna(pv_size) and float(pv_size) > 0))
        
        climate = row.get('in.ashrae_iecc_climate_zone_2004', 
                        row.get('in.building_america_climate_zone', 'Mixed-Humid'))
        
        home = {
            'id': int(row.get('bldg_id', idx + 1)),
            'location': location,
            'latitude': float(row.get('in.weather_file_latitude', 39.8)),
            'longitude': float(row.get('in.weather_file_longitude', -98.5)),
            'home_size': sqft,
            'bedrooms': bedrooms,
            'occupants': occupants,
            'home_type': _map_building_type(building_type),
            'heating_type': _map_heating_fuel(heating_fuel),
            'cooling_type': _map_cooling_type(cooling),
            'has_solar': has_solar,
            'monthly_usage': monthly_usage,
            'temperature': 15.0,
            'building_type_detail': str(building_type),
            'climate_zone': str(climate),
            'data_source': 'ResStock-NREL-Real'
        }
        
        success += 1
        
    except Exception as e:
        fail += 1
        error_type = type(e).__name__ + ": " + str(e)
        error_types[error_type] = error_types.get(error_type, 0) + 1

print(f"\n✅ Success: {success}")
print(f"❌ Failed: {fail}")
if error_types:
    print("\nError types:")
    for err, count in sorted(error_types.items(), key=lambda x: -x[1]):
        print(f"  {count}x: {err}")

os.remove(temp)
