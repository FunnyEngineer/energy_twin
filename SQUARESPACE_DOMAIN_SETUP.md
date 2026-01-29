# Using Your Squarespace Domain with Deployed Flask App

## Good News: Keep Your Domain on Squarespace!

You don't need to transfer anything. You can:
1. Keep domain registered with Squarespace
2. Deploy Flask app on Render/Railway/Heroku
3. Point your Squarespace domain to the deployed app

## Option 1: Point Domain to Deployed App (Recommended)

### Step 1: Deploy Your App

First, deploy to a hosting platform:

**Render.com (Recommended)**
1. Push code to GitHub
2. Deploy on Render.com (follow DEPLOY_NOW.md)
3. You'll get a URL like: `https://energy-twin-finder.onrender.com`

### Step 2: Configure Custom Domain on Render

1. In Render dashboard, go to your web service
2. Click "Settings" tab
3. Scroll to "Custom Domain" section
4. Click "Add Custom Domain"
5. Enter your Squarespace domain: `yourdomain.com` or `app.yourdomain.com`
6. Render will show DNS records you need to add

**Example DNS records Render provides:**
```
Type: CNAME
Name: app (or @)
Value: energy-twin-finder.onrender.com
```

### Step 3: Update DNS in Squarespace

1. Log into Squarespace
2. Go to **Settings** → **Domains** → Select your domain
3. Click **DNS Settings**
4. Click **Add Record**
5. Add the CNAME record from Render:
   - **Type**: CNAME
   - **Host**: `app` (for app.yourdomain.com) or `www` (for www.yourdomain.com)
   - **Data**: The value Render gave you (e.g., `energy-twin-finder.onrender.com`)
   - **TTL**: 3600

6. Save changes

### Step 4: Wait for DNS Propagation

- DNS changes take 5 minutes to 48 hours (usually ~1 hour)
- Your app will be live at: `https://app.yourdomain.com`

## Option 2: Use Subdomain (Cleaner Approach)

If you want to use Squarespace for your main site and the Flask app on a subdomain:

**Setup:**
- `yourdomain.com` → Squarespace website (marketing, info, etc.)
- `app.yourdomain.com` → Flask app on Render

**Benefits:**
- Professional landing page on Squarespace
- Full-featured app on separate subdomain
- Best of both worlds!

**Configuration:**
1. Keep Squarespace site at root domain (`yourdomain.com`)
2. Add CNAME record for subdomain:
   ```
   Type: CNAME
   Host: app
   Value: your-render-app.onrender.com
   TTL: 3600
   ```

## Option 3: Domain Forwarding (Simplest)

If you just want to redirect from Squarespace domain to your app:

1. In Squarespace: **Settings** → **Domains** → Your domain
2. Click **Domain Settings**
3. Enable **Domain Forwarding**
4. Enter your deployed app URL: `https://energy-twin-finder.onrender.com`
5. Choose redirect type: **301 Permanent** (recommended)

**Result:** When someone visits `yourdomain.com`, they're automatically redirected to your app.

## Step-by-Step Example

Let's say your domain is `energytwin.com`:

### Scenario A: App on Subdomain (Recommended)

1. **Deploy app to Render** → Get URL: `energy-twin-finder.onrender.com`

2. **In Render dashboard:**
   - Add custom domain: `app.energytwin.com`
   - Note the CNAME value they provide

3. **In Squarespace DNS:**
   - Add CNAME record:
     - Host: `app`
     - Data: `energy-twin-finder.onrender.com`

4. **Result:**
   - `energytwin.com` → Squarespace landing page (marketing, about, contact)
   - `app.energytwin.com` → Your Flask app
   - SSL automatically provided by Render

### Scenario B: Main Domain for App

1. **Deploy to Render** → Add custom domain: `energytwin.com`

2. **In Squarespace:**
   - Don't use Squarespace website
   - Go to DNS settings
   - Add Render's CNAME record

3. **Result:** `energytwin.com` → Your Flask app directly

## Recommended Approach

**Best setup:**

```
energytwin.com (Squarespace)
├── Homepage (landing page)
├── About page
├── Contact page
└── [LAUNCH APP button] → app.energytwin.com (Render/Railway)
```

**Why this works well:**
- Professional marketing site on Squarespace (easy to update)
- Powerful Flask app on proper hosting
- Clear separation of concerns
- Both use your custom domain

## DNS Configuration Cheatsheet

**For Render.com:**
```
Type: CNAME
Host: app
Data: your-app-name.onrender.com
```

**For Railway.app:**
```
Type: CNAME
Host: app  
Data: your-app-name.up.railway.app
```

**For Heroku:**
```
Type: CNAME
Host: app
Data: your-app-name.herokuapp.com
```

## Troubleshooting

**DNS not working?**
- Wait up to 24 hours for propagation
- Clear browser cache: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
- Check DNS propagation: https://dnschecker.org

**SSL certificate issues?**
- Most platforms (Render, Railway) auto-provision SSL
- May take 10-15 minutes after DNS is configured
- If issues persist, check platform's SSL settings

**Squarespace won't let me add CNAME?**
- Make sure you're in DNS Settings, not Domain Settings
- Remove any conflicting records with same host name
- Some Squarespace plans restrict DNS editing - check your plan

## Cost Summary

- **Squarespace domain**: Already paid ✅
- **Squarespace website**: Keep if you want marketing site (optional)
- **Render/Railway hosting**: FREE tier available
- **Total additional cost**: $0 (or $7/month for always-on service)

## Quick Start Commands

1. **Deploy to Render:**
   ```bash
   git init
   git add .
   git commit -m "Deploy to Render"
   git push origin main
   # Then connect on render.com
   ```

2. **Configure domain in Render** (after deployment)

3. **Add DNS record in Squarespace**

4. **Done!** Visit your custom domain

## Need Help?

- Render custom domains: https://render.com/docs/custom-domains
- Railway custom domains: https://docs.railway.app/deploy/custom-domains
- Squarespace DNS: https://support.squarespace.com/hc/en-us/articles/205812378-Connecting-a-Squarespace-domain-to-an-external-site

You'll be live at `https://yourdomain.com` or `https://app.yourdomain.com` in about an hour after setup!
