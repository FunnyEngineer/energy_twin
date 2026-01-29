# Find Your Energy Twins

A web application that helps you discover homes with similar energy usage patterns through machine learning and global energy visualization. **Now powered by real data from NREL's ResStock dataset!**

## Features

- 🌍 Global real-time weather and energy usage visualization
- 🏠 Interactive questionnaire to profile your home
- 🤖 ML-powered similarity matching to find your energy twins
- 📊 Beautiful data visualizations and insights
- 🏛️ **Real residential building data from NREL ResStock** - U.S. Department of Energy's comprehensive residential building stock model

## Data Source

This application uses data based on [ResStock](https://resstock.nrel.gov/) - the National Laboratory of the Rockies' highly granular, bottom-up model of the U.S. residential building stock. ResStock combines:

- Multiple public and private data sources
- Statistical sampling methods from RECS (Residential Energy Consumption Survey)
- Advanced building energy simulations
- Real climate zone distributions across the United States

The energy calculations are based on ResStock's validated models that account for:
- Building type and vintage
- Climate zones (Hot-Humid, Hot-Dry, Cold, Marine, etc.)
- Heating and cooling systems
- Occupancy patterns
- Real-world energy efficiency distributions

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
copy .env.example .env
# Edit .env and add your API keys
```

3. Run the application:
```bash
python app.py
```

4. Open your browser to `http://localhost:5000`

## API Keys

- Get a free OpenWeatherMap API key at: https://openweathermap.org/api

## Technology Stack

- Backend: Flask (Python)
- Frontend: HTML, CSS, JavaScript
- ML: scikit-learn
- Visualization: Leaflet.js, Chart.js
- Data: OpenWeatherMap API, sample energy dataset
