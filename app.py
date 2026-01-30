"""
Flask Application - Energy Twin Finder
Main backend API for finding energy twins using ML
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
import os
import numpy as np
from config import Config
from ml_model import EnergyTwinMatcher
from weather_service import WeatherService

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Initialize services
weather_service = WeatherService()
ml_matcher = EnergyTwinMatcher()

# Load homes data
HOMES_DATA = None  # Keep as DataFrame for efficiency
DATA_FILE = 'data/homes_data.parquet'


def convert_to_json_serializable(obj):
    """Convert numpy types to native Python types for JSON serialization"""
    if isinstance(obj, dict):
        return {key: convert_to_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_serializable(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    else:
        return obj


def load_homes_data():
    """Load homes data from parquet file - keep as DataFrame for efficiency"""
    global HOMES_DATA
    
    try:
        if os.path.exists(DATA_FILE):
            import pandas as pd
            # Keep as DataFrame - more efficient for large datasets
            HOMES_DATA = pd.read_parquet(DATA_FILE)
            print(f"✅ Loaded {len(HOMES_DATA):,} homes from ResStock parquet dataset")
            
            # Train the ML model
            if len(HOMES_DATA) > 0:
                ml_matcher.fit(HOMES_DATA)
                print("🤖 ML model trained successfully on ResStock data")
            else:
                print("⚠️  Warning: Data file is empty!")
        else:
            print("📥 No data file found. Generating ResStock data...")
            print(f"📂 Looking for: {os.path.abspath(DATA_FILE)}")
            print(f"📂 Current directory: {os.getcwd()}")
            print(f"📂 Directory exists: {os.path.exists('data/')}")
            
            from resstock_loader import ResStockDataLoader
            loader = ResStockDataLoader()
            HOMES_DATA = loader.download_sample_metadata(DATA_FILE, num_samples=1000)
            
            if len(HOMES_DATA) > 0:
                ml_matcher.fit(HOMES_DATA)
                print("✅ ResStock data generated and ML model trained")
            else:
                print("❌ Failed to generate data!")
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        import traceback
        traceback.print_exc()
        # Create minimal fallback data so app doesn't crash
        import pandas as pd
        HOMES_DATA = pd.DataFrame()


@app.route('/')
def index():
    """Render the main page with preloaded stats"""
    # Calculate stats from loaded data
    if HOMES_DATA is not None and len(HOMES_DATA) > 0:
        stats = {
            'total_homes': f"{len(HOMES_DATA):,}",
            'avg_energy': f"{HOMES_DATA['monthly_kwh'].mean():.0f} kWh/month",
            'cities': f"{HOMES_DATA['display_location'].nunique():,}"
        }
    else:
        stats = {
            'total_homes': "0",
            'avg_energy': "-- kWh/month",
            'cities': "0"
        }
    
    # Dev defaults (only for development)
    dev_defaults = None
    if Config.DEV_MODE:
        dev_defaults = {
            'location': 'Austin, TX',
            'home_size': '500',
            'bedrooms': '1',
            'occupants': '1',
            'building_type': '50 or more Unit',
            'heating_fuel': 'Natural Gas',
            'cooling_type': 'Central AC',
            'climate_zone': '2A',
            'has_solar': 'no'
        }
    
    return render_template('index.html', stats=stats, dev_defaults=dev_defaults)


@app.route('/api/global-data')
def get_global_data():
    """Get global energy data for map visualization - optimized with sampling"""
    
    if HOMES_DATA is None or len(HOMES_DATA) == 0:
        return jsonify({
            'success': False,
            'message': 'No data available',
            'homes': [],
            'stats': {'total_homes': 0, 'avg_energy': 0, 'cities': 0}
        })
    
    # Calculate statistics using full ResStock dataset
    total_homes = len(HOMES_DATA)
    avg_energy = HOMES_DATA['monthly_kwh'].mean()
    cities = HOMES_DATA['display_location'].nunique()
    
    stats = {
        'total_homes': int(total_homes),
        'avg_energy': round(float(avg_energy), 1),
        'cities': int(cities)
    }
    
    # OPTIMIZATION: Sample data for map display (10,000 homes instead of 549,971)
    # This dramatically reduces transfer size and rendering time
    sample_size = 10000
    if len(HOMES_DATA) > sample_size:
        # Random sample for geographic diversity
        sampled_df = HOMES_DATA.sample(n=sample_size, random_state=42)
    else:
        sampled_df = HOMES_DATA
    
    # Prepare lightweight data for map (only essential fields)
    homes_for_map = []
    for _, row in sampled_df.iterrows():
        home_data = {
            'id': int(row.get('bldg_id', 0)),
            'location': str(row.get('display_location', 'Unknown')),
            'lat': round(float(row.get('in.weather_file_latitude', 39.8)), 2),  # Round for smaller JSON
            'lon': round(float(row.get('in.weather_file_longitude', -98.5)), 2),
            'usage': int(row.get('monthly_kwh', 900)),
            'size': int(row.get('in.sqft..ft2', 1500)),
            'type': str(row.get('in.geometry_building_type_acs', 'Single-Family Detached')),
            'beds': int(row.get('in.bedrooms', 3)),
            'occupants': int(row.get('in.occupants', 2)),
        }
        homes_for_map.append(home_data)
    
    return jsonify({
        'success': True,
        'homes': homes_for_map,
        'stats': stats,
        'sample_info': {
            'displayed': len(homes_for_map),
            'total': total_homes,
            'note': f'Showing {len(homes_for_map):,} representative homes from {total_homes:,} total'
        }
    })


@app.route('/api/find-twins', methods=['POST'])
def find_twins():
    """Find energy twins for a user's home - using ResStock native format"""
    
    try:
        data = request.json
        
        # Parse user input and convert to ResStock format
        user_home = {
            # Use ResStock native column names
            'in.sqft..ft2': int(data.get('home_size', 1500)),
            'in.bedrooms': int(data.get('bedrooms', 3)),
            'in.occupants': int(data.get('occupants', 2)),
            'in.geometry_building_type_acs': data.get('building_type', 'Single-Family Detached'),
            'in.heating_fuel': data.get('heating_fuel', 'Electricity'),
            'in.hvac_cooling_type': data.get('cooling_type', 'Central AC'),
            'in.ashrae_iecc_climate_zone_2004': data.get('climate_zone', 'Mixed-Humid'),
            'display_location': data.get('location', 'USA'),
        }
        
        # Get monthly usage if provided
        monthly_usage = data.get('monthly_usage')
        if monthly_usage:
            user_home['monthly_kwh'] = float(monthly_usage)
        else:
            # Predict energy usage based on similar homes (ML-based)
            predicted_usage = ml_matcher.predict_energy_usage(user_home, HOMES_DATA, k=50)
            user_home['monthly_kwh'] = predicted_usage
            print(f"🔮 Predicted energy usage: {predicted_usage:.0f} kWh/month")
        
        # Solar panel
        has_solar = data.get('has_solar', 'No')
        user_home['has_solar_panel'] = (has_solar.lower() == 'yes')
        user_home['in.has_pv'] = 'Yes' if user_home['has_solar_panel'] else 'No'
        
        # Get k value
        k_value = int(data.get('k_value', 10))
        
        # Find similar homes using ML
        similar_homes = ml_matcher.find_similar_homes(user_home, HOMES_DATA, k=k_value)
        
        # Calculate insights
        insights = ml_matcher.calculate_insights(similar_homes, user_home)
        
        # Format similar homes for frontend
        twins_formatted = []
        for twin in similar_homes:
            twin_formatted = {
                'id': twin.get('bldg_id', 0),
                'location': twin.get('display_location', 'Unknown'),
                'latitude': twin.get('in.weather_file_latitude', 0),
                'longitude': twin.get('in.weather_file_longitude', 0),
                'home_size': int(twin.get('in.sqft..ft2', 1500)),
                'bedrooms': int(twin.get('in.bedrooms', 3)),
                'occupants': int(twin.get('in.occupants', 2)),
                'building_type': twin.get('in.geometry_building_type_acs', 'Unknown'),
                'heating_fuel': twin.get('in.heating_fuel', 'Unknown'),
                'cooling_type': twin.get('in.hvac_cooling_type', 'Unknown'),
                'monthly_usage': int(twin.get('monthly_kwh', 900)),
                'climate_zone': twin.get('in.ashrae_iecc_climate_zone_2004', 'Unknown'),
                'similarity_score': twin.get('similarity_score', 0),
                'state': twin.get('in.state', 'Unknown'),
                'timeseries_available': bool(twin.get('bldg_id') and twin.get('in.state'))
            }
            twins_formatted.append(twin_formatted)
        
        # Convert all numpy types to native Python types for JSON serialization
        user_home_clean = convert_to_json_serializable(user_home)
        twins_clean = convert_to_json_serializable(twins_formatted)
        insights_clean = convert_to_json_serializable(insights)
        
        return jsonify({
            'success': True,
            'user_profile': user_home_clean,
            'twins': twins_clean,
            'insights': insights_clean
        })
        
    except Exception as e:
        print(f"Error in find_twins: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400


def estimate_energy_usage(home):
    """Estimate energy usage based on home characteristics"""
    base_usage = home['home_size'] * 0.3
    base_usage += home['occupants'] * 50
    base_usage += home['bedrooms'] * 30
    
    # Adjust for heating type
    heating_multipliers = {'electric': 1.3, 'gas': 0.9, 'oil': 1.0, 'heat_pump': 0.8, 'other': 1.0}
    base_usage *= heating_multipliers.get(home['heating_type'], 1.0)
    
    # Adjust for cooling
    cooling_multipliers = {'central_ac': 1.2, 'window_ac': 1.1, 'heat_pump': 0.9, 'none': 0.8}
    base_usage *= cooling_multipliers.get(home['cooling_type'], 1.0)
    
    # Adjust for temperature
    temp = home.get('temperature', 20)
    if temp < 5 or temp > 30:
        base_usage *= 1.3
    elif temp < 10 or temp > 25:
        base_usage *= 1.15
    
    # Solar reduces usage
    if home.get('has_solar'):
        base_usage *= 0.7
    
    return int(base_usage)


@app.route('/api/weather/<city>')
def get_weather(city):
    """Get weather data for a city"""
    weather = weather_service.get_weather_by_city(city)
    return jsonify({
        'success': True,
        'weather': weather
    })


@app.route('/api/timeseries/<int:building_id>')
def get_timeseries(building_id):
    """Fetch and process timeseries data for a building"""
    try:
        import requests
        from io import BytesIO
        
        # Get building info from dataset
        building_row = HOMES_DATA[HOMES_DATA['bldg_id'] == building_id]
        if building_row.empty:
            return jsonify({
                'success': False,
                'message': 'Building not found'
            }), 404
        
        state = building_row.iloc[0].get('in.state', '')
        if not state:
            return jsonify({
                'success': False,
                'message': 'State information not available'
            }), 400
        
        # Construct S3 URL
        base_url = 'https://oedi-data-lake.s3.amazonaws.com/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2025/resstock_amy2018_release_1'
        timeseries_url = f"{base_url}/timeseries_individual_buildings/by_state/upgrade=0/state={state}/{building_id}-0.parquet"
        
        print(f"📊 Fetching timeseries from: {timeseries_url}")
        
        # Download timeseries data
        response = requests.get(timeseries_url, timeout=60)
        if response.status_code != 200:
            return jsonify({
                'success': False,
                'message': f'Timeseries data not available (HTTP {response.status_code})'
            }), response.status_code
        
        # Parse parquet
        import pandas as pd
        df = pd.read_parquet(BytesIO(response.content))
        
        # Process data for visualization
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Calculate total electricity usage
        electricity_cols = [col for col in df.columns if 'out.electricity.' in col and 'energy_consumption' in col]
        df['total_electricity_kwh'] = df[electricity_cols].sum(axis=1)
        
        # Aggregate to daily data for easier visualization
        df['date'] = df['timestamp'].dt.date
        daily_data = df.groupby('date').agg({
            'total_electricity_kwh': 'sum'
        }).reset_index()
        
        # Also get hourly averages by hour of day (typical day pattern)
        df['hour'] = df['timestamp'].dt.hour
        hourly_pattern = df.groupby('hour').agg({
            'total_electricity_kwh': 'mean'
        }).reset_index()
        
        # Get monthly totals
        df['month'] = df['timestamp'].dt.to_period('M')
        monthly_data = df.groupby('month').agg({
            'total_electricity_kwh': 'sum'
        }).reset_index()
        monthly_data['month'] = monthly_data['month'].astype(str)
        
        # Get breakdown by end use (monthly averages)
        end_use_breakdown = {}
        for col in electricity_cols:
            end_use_name = col.replace('out.electricity.', '').replace('.energy_consumption..kwh', '').replace('_', ' ').title()
            monthly_avg = df.groupby('month')[col].sum().mean()
            end_use_breakdown[end_use_name] = round(float(monthly_avg), 2)
        
        return jsonify({
            'success': True,
            'building_id': int(building_id),
            'state': state,
            'data': {
                'daily': daily_data.to_dict('records'),
                'hourly_pattern': hourly_pattern.to_dict('records'),
                'monthly': monthly_data.to_dict('records'),
                'end_use_breakdown': end_use_breakdown
            },
            'stats': {
                'total_annual_kwh': round(float(df['total_electricity_kwh'].sum()), 2),
                'avg_daily_kwh': round(float(daily_data['total_electricity_kwh'].mean()), 2),
                'peak_daily_kwh': round(float(daily_data['total_electricity_kwh'].max()), 2),
                'min_daily_kwh': round(float(daily_data['total_electricity_kwh'].min()), 2)
            }
        })
        
    except Exception as e:
        print(f"❌ Error fetching timeseries: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# Load data when module is imported (works with both direct run and gunicorn)
load_homes_data()

if __name__ == '__main__':
    # Run the application directly (not used by gunicorn)
    print(f"\n{'='*70}")
    print(f"🌍 Energy Twin Finder Server Starting...")
    print(f"{'='*70}")
    print(f"📍 URL: http://localhost:{Config.PORT}")
    print(f"🏠 Total homes in database: {len(HOMES_DATA)}")
    print(f"📊 Data source: NREL ResStock (U.S. Residential Building Stock)")
    print(f"🤖 ML model: Ready")
    print(f"{'='*70}\n")
    
    app.run(host='0.0.0.0', port=Config.PORT, debug=Config.DEBUG, use_reloader=False)
