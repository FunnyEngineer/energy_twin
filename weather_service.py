"""
Weather API integration using OpenWeatherMap
"""

import requests
from config import Config


class WeatherService:
    """Service for fetching weather data"""
    
    def __init__(self):
        self.api_key = Config.WEATHER_API_KEY
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"
    
    def get_weather_by_city(self, city_name):
        """Get current weather for a city"""
        if not self.api_key:
            # Return mock data if no API key
            return self._get_mock_weather()
        
        try:
            params = {
                'q': city_name,
                'appid': self.api_key,
                'units': 'metric'
            }
            response = requests.get(self.base_url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'temperature': round(data['main']['temp'], 1),
                    'humidity': data['main']['humidity'],
                    'description': data['weather'][0]['description'],
                    'city': data['name']
                }
            else:
                return self._get_mock_weather()
        except Exception as e:
            print(f"Weather API error: {e}")
            return self._get_mock_weather()
    
    def get_weather_by_coords(self, lat, lon):
        """Get current weather for coordinates"""
        if not self.api_key:
            return self._get_mock_weather()
        
        try:
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric'
            }
            response = requests.get(self.base_url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'temperature': round(data['main']['temp'], 1),
                    'humidity': data['main']['humidity'],
                    'description': data['weather'][0]['description']
                }
            else:
                return self._get_mock_weather()
        except Exception as e:
            print(f"Weather API error: {e}")
            return self._get_mock_weather()
    
    def _get_mock_weather(self):
        """Return mock weather data when API is unavailable"""
        import random
        return {
            'temperature': round(random.uniform(10, 25), 1),
            'humidity': random.randint(40, 80),
            'description': 'partly cloudy'
        }
