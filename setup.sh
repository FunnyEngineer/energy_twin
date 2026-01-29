#!/bin/bash
# Setup script for Energy Twin Finder

echo "🌍 Setting up Energy Twin Finder..."
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
python -m venv venv

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo ""
    echo "⚠️  Please edit .env and add your OpenWeatherMap API key"
    echo "   Get a free key at: https://openweathermap.org/api"
fi

# Generate sample data
echo "🏠 Generating sample home data..."
python generate_data.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo "  1. Activate virtual environment:"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "     venv\\Scripts\\activate"
else
    echo "     source venv/bin/activate"
fi
echo "  2. Run the server:"
echo "     python app.py"
echo "  3. Open http://localhost:5000 in your browser"
echo ""
