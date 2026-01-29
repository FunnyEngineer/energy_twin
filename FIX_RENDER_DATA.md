# Quick Fix Commands for Render Deployment

## The Issue
The data file exists locally but may not be loading properly on Render.

## Solution: Update and Redeploy

Run these commands:

```bash
# Make sure you're in the project directory
cd D:\energy_twin

# Add all changes
git add .

# Commit the fixes
git commit -m "Fix data loading and Python version for Render"

# Push to GitHub (triggers auto-deploy on Render)
git push origin main
```

## What Was Fixed:

1. **✅ Enhanced error logging** - App now shows detailed info about data loading
2. **✅ Updated Python version** - Changed to 3.11.11 (more stable)
3. **✅ Added build script** - Verifies data file during build
4. **✅ Better error handling** - App won't crash if data missing

## After Pushing:

1. Go to your Render dashboard
2. Watch the deployment logs
3. Look for these messages:
   - "✅ data/homes_data.parquet exists"
   - "✅ Loaded 987 homes from ResStock parquet dataset"
   - "🤖 ML model trained successfully"

## If Data Still Missing on Render:

The data file should be in Git. Verify:
```bash
git ls-files data/
# Should show: data/homes_data.parquet
```

If not shown, add it explicitly:
```bash
git add -f data/homes_data.parquet
git commit -m "Add data file explicitly"
git push origin main
```

## Check Build Configuration on Render:

In Render dashboard → Your service → Settings:

**Build Command:** Should be one of:
- `./build.sh` (if using custom script)
- `pip install -r requirements.txt` (standard)

**Start Command:** Should be:
- `gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120`

## Monitor Deployment:

After pushing, check Render logs for:
```
✅ data/homes_data.parquet exists
Size: 40K
✅ Loaded 987 homes from ResStock parquet dataset
🤖 ML model trained successfully on ResStock data
```

Then test: https://energy-twin.onrender.com

The map should now show 987 data points!
