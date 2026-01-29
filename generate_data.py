"""
Generate sample energy and home data for the database
"""

import json
import random
import numpy as np


# Sample cities with coordinates and typical temperatures
CITIES = [
    {"name": "New York, USA", "lat": 40.7128, "lon": -74.0060, "temp_range": (5, 25)},
    {"name": "Los Angeles, USA", "lat": 34.0522, "lon": -118.2437, "temp_range": (15, 30)},
    {"name": "Chicago, USA", "lat": 41.8781, "lon": -87.6298, "temp_range": (0, 28)},
    {"name": "Miami, USA", "lat": 25.7617, "lon": -80.1918, "temp_range": (20, 32)},
    {"name": "Seattle, USA", "lat": 47.6062, "lon": -122.3321, "temp_range": (8, 22)},
    {"name": "London, UK", "lat": 51.5074, "lon": -0.1278, "temp_range": (5, 20)},
    {"name": "Paris, France", "lat": 48.8566, "lon": 2.3522, "temp_range": (5, 25)},
    {"name": "Berlin, Germany", "lat": 52.5200, "lon": 13.4050, "temp_range": (0, 25)},
    {"name": "Tokyo, Japan", "lat": 35.6762, "lon": 139.6503, "temp_range": (5, 30)},
    {"name": "Sydney, Australia", "lat": -33.8688, "lon": 151.2093, "temp_range": (10, 28)},
    {"name": "Toronto, Canada", "lat": 43.6532, "lon": -79.3832, "temp_range": (-5, 26)},
    {"name": "Singapore", "lat": 1.3521, "lon": 103.8198, "temp_range": (25, 32)},
    {"name": "Dubai, UAE", "lat": 25.2048, "lon": 55.2708, "temp_range": (20, 40)},
    {"name": "Mumbai, India", "lat": 19.0760, "lon": 72.8777, "temp_range": (20, 35)},
    {"name": "São Paulo, Brazil", "lat": -23.5505, "lon": -46.6333, "temp_range": (15, 28)},
    {"name": "Mexico City, Mexico", "lat": 19.4326, "lon": -99.1332, "temp_range": (12, 26)},
    {"name": "Cairo, Egypt", "lat": 30.0444, "lon": 31.2357, "temp_range": (15, 35)},
    {"name": "Moscow, Russia", "lat": 55.7558, "lon": 37.6173, "temp_range": (-10, 25)},
    {"name": "Beijing, China", "lat": 39.9042, "lon": 116.4074, "temp_range": (-5, 32)},
    {"name": "Istanbul, Turkey", "lat": 41.0082, "lon": 28.9784, "temp_range": (5, 30)},
]

HOME_TYPES = ['apartment', 'house', 'townhouse', 'condo']
HEATING_TYPES = ['electric', 'gas', 'oil', 'heat_pump', 'other']
COOLING_TYPES = ['central_ac', 'window_ac', 'heat_pump', 'none']


def generate_home_data(num_homes=100):
    """Generate realistic home energy data"""
    homes = []
    
    for i in range(num_homes):
        city = random.choice(CITIES)
        home_type = random.choice(HOME_TYPES)
        bedrooms = random.randint(1, 5)
        
        # Home size correlates with bedrooms
        if home_type == 'apartment':
            base_size = 600 + (bedrooms - 1) * 300
        elif home_type == 'house':
            base_size = 1000 + (bedrooms - 1) * 400
        elif home_type == 'townhouse':
            base_size = 800 + (bedrooms - 1) * 350
        else:  # condo
            base_size = 700 + (bedrooms - 1) * 300
        
        home_size = base_size + random.randint(-200, 200)
        
        # Occupants correlate with bedrooms
        occupants = min(bedrooms, random.randint(1, bedrooms + 1))
        
        heating_type = random.choice(HEATING_TYPES)
        cooling_type = random.choice(COOLING_TYPES)
        has_solar = random.random() < 0.15  # 15% have solar
        
        # Current temperature
        temp_min, temp_max = city['temp_range']
        temperature = round(random.uniform(temp_min, temp_max), 1)
        
        # Calculate energy usage based on various factors
        base_usage = home_size * 0.3  # Base on home size
        base_usage += occupants * 50  # Add per occupant
        base_usage += bedrooms * 30  # Add per bedroom
        
        # Adjust for heating type
        heating_multipliers = {'electric': 1.3, 'gas': 0.9, 'oil': 1.0, 'heat_pump': 0.8, 'other': 1.0}
        base_usage *= heating_multipliers[heating_type]
        
        # Adjust for cooling
        cooling_multipliers = {'central_ac': 1.2, 'window_ac': 1.1, 'heat_pump': 0.9, 'none': 0.8}
        base_usage *= cooling_multipliers[cooling_type]
        
        # Adjust for temperature (extreme temps increase usage)
        if temperature < 5 or temperature > 30:
            base_usage *= 1.3
        elif temperature < 10 or temperature > 25:
            base_usage *= 1.15
        
        # Solar reduces usage
        if has_solar:
            base_usage *= 0.7
        
        # Add some randomness
        monthly_usage = int(base_usage * random.uniform(0.8, 1.2))
        
        home = {
            'id': i + 1,
            'location': city['name'],
            'latitude': city['lat'] + random.uniform(-0.5, 0.5),
            'longitude': city['lon'] + random.uniform(-0.5, 0.5),
            'home_size': home_size,
            'bedrooms': bedrooms,
            'occupants': occupants,
            'home_type': home_type,
            'heating_type': heating_type,
            'cooling_type': cooling_type,
            'has_solar': has_solar,
            'monthly_usage': monthly_usage,
            'temperature': temperature
        }
        
        homes.append(home)
    
    return homes


def save_sample_data(filepath='data/homes_data.json', num_homes=100):
    """Generate and save sample data"""
    homes = generate_home_data(num_homes)
    
    with open(filepath, 'w') as f:
        json.dump(homes, f, indent=2)
    
    print(f"Generated {num_homes} homes and saved to {filepath}")
    return homes


if __name__ == '__main__':
    import os
    os.makedirs('data', exist_ok=True)
    save_sample_data('data/homes_data.json', num_homes=150)
