# Quick Deployment to Render.com (Free Hosting)

## Step 1: Prepare Your Code

Your app is ready! These files have been created:
- `Procfile` - Tells Render how to start your app
- `runtime.txt` - Specifies Python 3.11 (for compatibility)
- `requirements.txt` - Updated with gunicorn and flexible versions
- `README_DEPLOYMENT.md` - Full deployment guide

## Step 2: Push to GitHub

```bash
# Initialize git (if not done)
git init

# Add all files
git add .

# Commit
git commit -m "Ready for deployment"

# Create repository on GitHub.com, then:
git remote add origin https://github.com/YOUR_USERNAME/energy-twin-finder.git
git branch -M main
git push -u origin main
```

## Step 3: Deploy on Render.com

1. **Sign up**: Go to https://render.com and sign up with GitHub

2. **Create Web Service**:
   - Click "New +" button → "Web Service"
   - Connect your GitHub repository
   - Select your `energy-twin-finder` repository

3. **Configure**:
   - **Name**: `energy-twin-finder` (or your choice)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Instance Type**: Free

4. **Environment Variables** (Optional):
   - Click "Advanced" → "Add Environment Variable"
   - Add: `FLASK_ENV` = `production`

5. **Deploy**:
   - Click "Create Web Service"
   - Wait 5-10 minutes for first deployment
   - Your app will be live at: `https://energy-twin-finder.onrender.com`

## ⚠️ Important Notes

### About Free Tier
- Render free tier spins down after 15 minutes of inactivity
- First request after inactivity may take 30-60 seconds
- Perfect for demos and testing
- Upgrade to paid tier ($7/month) for always-on service

### About Squarespace
**Squarespace CANNOT host this Flask app** because:
- Squarespace only hosts static websites (HTML/CSS/JS)
- Your app needs Python runtime and a backend server
- Squarespace doesn't support server-side applications

**What you CAN do**:
1. Deploy app on Render/Railway/Heroku
2. Use Squarespace for your marketing website
3. Link from Squarespace → Your hosted app
   Example: Add a button "Launch App" → https://your-app.onrender.com

## Alternative: Railway.app (Even Easier)

1. Go to https://railway.app
2. Sign in with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway auto-detects and deploys!
6. Live in 2-3 minutes

## Testing Locally

Your server is now running at: **http://localhost:5000**

To restart it later:
```bash
cd D:\energy_twin
D:/energy_twin/.venv/Scripts/python.exe app.py
```

Or use the script:
```powershell
.\run_server.ps1
```

## Next Steps

1. Test locally: http://localhost:5000
2. Push code to GitHub
3. Deploy to Render.com (follow steps above)
4. Share your live URL!

## Need Help?

- Render docs: https://render.com/docs/web-services
- Railway docs: https://docs.railway.app
- See `README_DEPLOYMENT.md` for more options
