# Deployment Guide

## Overview

This app consists of two parts that deploy separately:
- **Frontend**: Next.js app → Vercel
- **Backend**: FastAPI Python app → Render.com

## 🚀 Quick Deploy

### 1. Backend Deployment (Render.com)

1. Go to [render.com](https://render.com) and sign in with GitHub
2. Click **"New +"** → **"Web Service"**
3. Connect to this repository: `market-research`
4. Render will auto-detect the `render.yaml` configuration
5. Add environment variables:
   - `ALPHA_VANTAGE_API_KEY` - Your Alpha Vantage API key
   - `NEWS_API_KEY` - Your News API key
   - `REDDIT_CLIENT_ID` - Reddit app client ID
   - `REDDIT_CLIENT_SECRET` - Reddit app secret
   - `REDDIT_USER_AGENT` - Reddit user agent string
6. Click **"Create Web Service"**
7. Copy the deployed URL (e.g., `https://market-research-backend.onrender.com`)

**Note**: Free tier spins down after 15 minutes of inactivity (cold starts may take 30-60 seconds).

### 2. Frontend Deployment (Vercel)

#### Option A: Via Vercel Dashboard (Recommended)
1. Go to [vercel.com](https://vercel.com) and sign in with GitHub
2. Click **"Add New Project"**
3. Import the `market-research` repository
4. Vercel auto-detects Next.js configuration from `vercel.json`
5. Add environment variable:
   - `NEXT_PUBLIC_API_URL` = `https://your-backend-url.onrender.com` (from step 1.7)
6. Click **"Deploy"**

#### Option B: Via Vercel CLI
```bash
npm i -g vercel
cd frontend
vercel --prod
```

## 🔄 Continuous Deployment

Both platforms are now configured for **automatic deployments**:
- **Push to GitHub** → Automatically triggers new deployments on both Render and Vercel
- **No manual steps needed** - just `git push` and both frontend/backend redeploy

## 📝 Environment Variables

### Backend (.env - Render.com)
```bash
ALPHA_VANTAGE_API_KEY=your_key_here
NEWS_API_KEY=your_key_here
REDDIT_CLIENT_ID=your_id_here
REDDIT_CLIENT_SECRET=your_secret_here
REDDIT_USER_AGENT=your_agent_here
ENVIRONMENT=production
```

### Frontend (.env.local - Vercel)
```bash
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
```

## 🛠️ Updating Your Deployment

Whenever you want to deploy updates:

```bash
# 1. Make your changes
# 2. Commit and push
git add .
git commit -m "Your update message"
git push origin main

# Both frontend and backend will automatically redeploy!
```

## 🔍 Monitoring

- **Vercel Dashboard**: https://vercel.com/dashboard - Check frontend logs, deployments, analytics
- **Render Dashboard**: https://dashboard.render.com - Check backend logs, health, metrics

## 💡 Tips

- **First deployment takes ~5 minutes** for each platform
- **Subsequent deployments take ~2 minutes**
- **Render free tier** may have cold starts - upgrade to paid ($7/mo) for always-on
- **Check logs** if deployment fails - usually missing environment variables

## 🆘 Troubleshooting

### Backend won't start
- Check environment variables are set in Render dashboard
- Check logs: Render Dashboard → Your Service → Logs

### Frontend can't connect to backend
- Verify `NEXT_PUBLIC_API_URL` in Vercel environment variables
- Check CORS settings in backend `main.py` include your Vercel domain
- Redeploy frontend after updating env vars

### Scheduled jobs not running
- Render free tier may spin down - upgrade to paid tier for 24/7 uptime
- Check APScheduler logs in Render dashboard
