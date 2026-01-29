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
HOMES_DATA = []
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
    """Load homes data from parquet file"""
    global HOMES_DATA
    
    try:
        if os.path.exists(DATA_FILE):
            import pandas as pd
            df = pd.read_parquet(DATA_FILE)
            HOMES_DATA = df.to_dict('records')
            print(f"✅ Loaded {len(HOMES_DATA)} homes from ResStock parquet dataset")
            
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
            df = loader.download_sample_metadata(DATA_FILE, num_samples=1000)
            HOMES_DATA = df.to_dict('records')
            
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
        HOMES_DATA = []


@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')


@app.route('/api/global-data')
def get_global_data():
    """Get global energy data for map visualization"""
    
    # Calculate statistics
    total_homes = len(HOMES_DATA)
    avg_energy = sum(h['monthly_usage'] for h in HOMES_DATA) / total_homes if total_homes > 0 else 0
    # Count unique cities (all data is from USA)
    cities = len(set(h['location'] for h in HOMES_DATA))
    
    stats = {
        'total_homes': total_homes,
        'avg_energy': avg_energy,
        'cities': cities
    }
    
    return jsonify({
        'success': True,
        'homes': HOMES_DATA,
        'stats': stats
    })


@app.route('/api/find-twins', methods=['POST'])
def find_twins():
    """Find energy twins for a user's home"""
    
    try:
        data = request.json
        
        # Parse user input
        user_home = {
            'location': data.get('location', ''),
            'home_size': int(data.get('home_size', 0)),
            'bedrooms': int(data.get('bedrooms', 2)),
            'occupants': int(data.get('occupants', 2)),
            'home_type': data.get('home_type', 'apartment'),
            'heating_type': data.get('heating_type', 'electric'),
            'cooling_type': data.get('cooling_type', 'central_ac'),
            'has_solar': 1 if data.get('has_solar') == 'yes' else 0,
        }
        
        # Get monthly usage if provided
        monthly_usage = data.get('monthly_usage')
        if monthly_usage:
            user_home['monthly_usage'] = int(monthly_usage)
        
        # Get weather data for user's location
        weather = weather_service.get_weather_by_city(user_home['location'])
        user_home['temperature'] = weather['temperature']
        
        # Estimate energy usage if not provided
        if 'monthly_usage' not in user_home:
            user_home['monthly_usage'] = estimate_energy_usage(user_home)
        
        # Get k value
        k_value = int(data.get('k_value', 10))
        
        # Find similar homes using ML
        similar_homes = ml_matcher.find_similar_homes(user_home, HOMES_DATA, k=k_value)
        
        # Calculate insights
        insights = ml_matcher.calculate_insights(similar_homes, user_home)
        
        # Convert all numpy types to native Python types for JSON serialization
        user_home_clean = convert_to_json_serializable(user_home)
        similar_homes_clean = convert_to_json_serializable(similar_homes)
        insights_clean = convert_to_json_serializable(insights)
        
        return jsonify({
            'success': True,
            'user_profile': user_home_clean,
            'twins': similar_homes_clean,
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
