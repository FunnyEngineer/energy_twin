# Energy Twin Finder - Deployment Guide

## ⚠️ Important Note About Squarespace

**Squarespace cannot host Flask/Python applications.** Squarespace is a website builder for static content only and doesn't support:
- Python runtime
- Backend servers (Flask, Django, etc.)
- Custom server applications

## Recommended Deployment Options

### Option 1: Render.com (Recommended - Free Tier Available)
**Best for: Quick deployment with free hosting**

1. Create account at https://render.com
2. Connect your GitHub repository
3. Create new Web Service
4. Configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
5. Add environment variables (if needed)

### Option 2: Railway.app (Easy Deployment)
**Best for: Simple deployment with GitHub integration**

1. Sign up at https://railway.app
2. Create new project
3. Deploy from GitHub
4. Railway auto-detects Flask app
5. Automatic HTTPS and custom domains

### Option 3: PythonAnywhere (Python-Specific)
**Best for: Python-focused hosting**

1. Create account at https://www.pythonanywhere.com
2. Upload your code or clone from GitHub
3. Configure web app with Flask
4. Set up virtual environment
5. Free tier available

### Option 4: Heroku (Traditional Platform)
**Best for: Established platform with add-ons**

1. Install Heroku CLI
2. Create `Procfile`: `web: gunicorn app:app`
3. Commands:
   ```bash
   heroku login
   heroku create energy-twin-finder
   git push heroku main
   ```

### Option 5: Google Cloud Run / AWS Elastic Beanstalk
**Best for: Scalable production deployment**

For production-grade hosting with auto-scaling.

## Squarespace Alternative

If you want to use Squarespace for your main website, you can:
1. Host the Flask app on one of the platforms above
2. Use Squarespace for marketing/landing pages
3. Link from Squarespace to your app (e.g., "Launch App" button → https://your-app.render.com)
4. Or embed the app in an iframe on Squarespace (limited)

## Deployment Preparation

### 1. Create Procfile
```
web: gunicorn app:app --bind 0.0.0.0:$PORT
```

### 2. Update requirements.txt
Add gunicorn:
```
gunicorn==21.2.0
```

### 3. Configure for Production
Update `config.py` to read PORT from environment:
```python
PORT = int(os.environ.get('PORT', 5000))
```

### 4. Environment Variables
Set these on your hosting platform:
- `FLASK_ENV=production`
- `WEATHER_API_KEY=your_key_here` (if using OpenWeatherMap)

## Quick Start with Render.com (Step-by-Step)

1. **Push to GitHub** (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/energy-twin-finder.git
   git push -u origin main
   ```

2. **Sign up at Render.com**
   - Go to https://render.com
   - Sign up with GitHub
   
3. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your repository
   - Configure:
     - Name: `energy-twin-finder`
     - Environment: `Python 3`
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT`
     
4. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (5-10 minutes)
   - Your app will be live at: `https://energy-twin-finder.onrender.com`

## Local Development

To run locally:
```bash
# Windows PowerShell
.\run_server.ps1

# Or directly
D:/energy_twin/.venv/Scripts/python.exe app.py
```

Then open: http://localhost:5000

## Troubleshooting

**Port conflicts:** Change PORT in `.env` file
**Data not loading:** Ensure `data/homes_data.parquet` exists
**API errors:** Check server logs in terminal
**Module errors:** Run `pip install -r requirements.txt`

## Support

For deployment issues:
- Render: https://render.com/docs
- Railway: https://docs.railway.app
- PythonAnywhere: https://help.pythonanywhere.com
