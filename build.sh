#!/bin/bash
# Render build script

echo "===== Build Script Starting ====="
echo "Python version: $(python --version)"
echo "Current directory: $(pwd)"
echo "Contents:"
ls -la

echo ""
echo "===== Installing Python Dependencies ====="
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "===== Checking Data Directory ====="
if [ -d "data" ]; then
    echo "✅ data/ directory exists"
    ls -lh data/
    if [ -f "data/homes_data.parquet" ]; then
        echo "✅ data/homes_data.parquet exists"
        echo "Size: $(du -h data/homes_data.parquet)"
    else
        echo "❌ data/homes_data.parquet NOT found"
    fi
else
    echo "❌ data/ directory NOT found"
    echo "Creating data directory..."
    mkdir -p data
fi

echo ""
echo "===== Build Complete ====="
