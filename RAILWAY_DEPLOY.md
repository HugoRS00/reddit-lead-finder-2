# 🚄 Railway Deployment Guide

Deploy your Reddit Lead Finder to Railway.com in 5 minutes!

## Prerequisites

✅ GitHub account  
✅ Railway account (sign up at https://railway.app/)  
✅ Reddit API credentials  
✅ (Optional) Anthropic API key  

## Step-by-Step Deployment

### 1. Push to GitHub

```bash
cd reddit_lead_finder_v2
git init
git add .
git commit -m "Initial commit: Reddit Lead Finder v2.0"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/reddit-lead-finder-v2.git
git push -u origin main
```

### 2. Create Railway Project

1. Go to https://railway.app/
2. Click **"Start a New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub
5. Select your `reddit-lead-finder-v2` repository
6. Railway will automatically detect it's a Python app!

### 3. Add Environment Variables

In Railway dashboard, click on your service, then go to **"Variables"** tab:

**Required:**
```
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_secret
REDDIT_USER_AGENT=TradingWizard Lead Finder v2.0
```

**Optional (but recommended):**
```
ANTHROPIC_API_KEY=your_anthropic_api_key
PORT=5000
```

### 4. Deploy!

Railway will automatically:
- Install dependencies from `requirements.txt`
- Start the app using the `Procfile`
- Assign a public URL

**Your app will be live at**: `https://your-app.up.railway.app`

## 🔄 Automatic Deployments

Every time you push to GitHub, Railway automatically deploys!

```bash
git add .
git commit -m "Update feature"
git push
```

Railway will redeploy in ~1-2 minutes.

## 📊 Monitoring

### View Logs
1. Go to Railway dashboard
2. Click on your service
3. Go to **"Deployments"** tab
4. Click on latest deployment
5. View real-time logs

### Check Health
Visit: `https://your-app.up.railway.app/health`

Should return: `{"status": "healthy"}`

## ⚙️ Custom Domain (Optional)

1. Go to **"Settings"** tab in Railway
2. Click **"Generate Domain"** or add your custom domain
3. Railway provides free `.up.railway.app` domains
4. For custom domains, add CNAME record in your DNS

## 💰 Pricing

- **Starter Plan**: $5/month with $5 included credit
- **Pay as you go** for usage beyond credit
- Typical usage: $0-10/month for moderate traffic

## 🔧 Troubleshooting

### Build Failed
- Check `requirements.txt` is valid
- Ensure all dependencies are compatible
- Check Railway build logs

### App Crashes on Start
- Verify environment variables are set correctly
- Check that `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` are valid
- Review Railway logs for error messages

### "Port already in use"
- Railway automatically sets `PORT` environment variable
- App.py uses `os.getenv('PORT', 5000)` to handle this

### AI Replies Not Working
- Check `ANTHROPIC_API_KEY` is set correctly
- Verify API key is active at https://console.anthropic.com/
- App will fall back to templates if API key is invalid

## 🚀 Alternative: Render.com

If you prefer Render.com:

1. Go to https://render.com/
2. Click **"New"** → **"Web Service"**
3. Connect GitHub repository
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Environment**: Python 3
5. Add environment variables
6. Deploy!

## 📝 Post-Deployment Checklist

- [ ] App is accessible at Railway URL
- [ ] Health endpoint returns healthy status
- [ ] Can start a scan successfully
- [ ] AI reply generation works (or templates as fallback)
- [ ] All environment variables are set
- [ ] Logs show no errors

## 🎯 Next Steps

1. **Test Your App**: Run a scan and generate a reply
2. **Share the URL**: Use it from any device
3. **Monitor Usage**: Check Railway dashboard regularly
4. **Update Keywords**: Customize `config.json` and push
5. **Track Results**: Note which approaches work best

## 💡 Pro Tips

- **Set up monitoring**: Use Railway's built-in metrics
- **Enable auto-scaling**: Railway handles this automatically
- **Use custom domain**: Makes it more professional
- **Set resource limits**: Prevent unexpected bills
- **Review logs regularly**: Catch issues early

## 🆘 Need Help?

- **Railway Docs**: https://docs.railway.app/
- **Railway Discord**: https://discord.gg/railway
- **GitHub Issues**: Open an issue in your repo

---

**That's it! Your Reddit Lead Finder is now deployed and accessible worldwide! 🌍**
