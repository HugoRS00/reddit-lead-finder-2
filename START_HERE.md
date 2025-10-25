# 🎯 START HERE - Reddit Lead Finder v2.0

Welcome! This is a complete rebuild with a beautiful web interface, AI-powered replies, and comment search. Let's get you running in 5 minutes!

## What You've Got 🎁

A professional web application that:
- ✅ Searches Reddit posts AND comments
- ✅ Beautiful web interface (no command line needed!)
- ✅ Generates AI-powered replies with Claude
- ✅ One-click copy and paste
- ✅ Real-time statistics
- ✅ Deploy-ready for Railway.com

## Quick Start Options

### Option 1: Run Locally (5 minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up credentials
cp .env.example .env
# Edit .env and add your Reddit credentials

# 3. Run the app
python app.py

# 4. Open browser
# Go to: http://localhost:5000
```

### Option 2: Deploy to Railway (5 minutes)

```bash
# 1. Push to GitHub
git init
git add .
git commit -m "Initial commit"
git push

# 2. Deploy on Railway
# - Go to railway.app
# - Click "Deploy from GitHub"
# - Select your repo
# - Add environment variables
# - Done!
```

See **RAILWAY_DEPLOY.md** for detailed instructions.

## Getting API Keys

### Reddit API (Required)

1. Go to https://www.reddit.com/prefs/apps
2. Click "create another app..."
3. Type: **script**
4. Redirect URI: `http://localhost:8080`
5. Copy `client_id` and `client_secret`

### Anthropic API (Optional but Recommended)

1. Go to https://console.anthropic.com/
2. Create API key
3. Copy your key

**Note**: Without Anthropic key, app uses template replies (still works!)

## File Structure

```
reddit_lead_finder_v2/
├── app.py              ← Flask web application
├── main.py             ← Core Reddit search logic
├── config.json         ← Keywords and settings
├── .env.example        ← Credentials template
├── requirements.txt    ← Python dependencies
├── Procfile            ← Railway deployment
├── railway.json        ← Railway config
├── templates/
│   └── index.html      ← Web UI
├── test_setup.py       ← Test your setup
└── README.md           ← Full documentation
```

## How to Use the Web App

### 1. Select Keywords
- Purple = selected, Gray = not selected
- Click tags to toggle
- All selected by default

### 2. Set Options
- Date range: 1-30 days (default 7)
- Toggle comment search on/off

### 3. Start Scan
- Click "🔍 Start Scan"
- Wait 10-30 seconds

### 4. Review Results
- See posts and comments
- Sorted by relevance score
- Color-coded by quality

### 5. Generate Reply
- Click "✨ Generate AI Reply"
- Wait 2-3 seconds
- Review the AI-generated reply

### 6. Copy & Post
- Click "📋 Copy Reply"
- Click "🔗 Open in Reddit"
- Paste and post!

## What's New in v2.0?

🎨 **Web UI** - No more command line!  
🔍 **Comment Search** - 2x more opportunities  
🤖 **AI Replies** - Claude-powered generation  
⚡ **Faster** - 5x faster workflow  
🚀 **Easy Deploy** - Railway, Render, Heroku  

See **V2_HIGHLIGHTS.md** for full comparison.

## Testing Your Setup

```bash
python test_setup.py
```

This checks:
- ✅ All packages installed
- ✅ Config file valid
- ✅ Environment variables set
- ✅ Reddit API working
- ✅ Flask app ready

## Environment Variables

### Local Development (.env file)
```
REDDIT_CLIENT_ID=your_id
REDDIT_CLIENT_SECRET=your_secret
REDDIT_USER_AGENT=TradingWizard Lead Finder v2.0
ANTHROPIC_API_KEY=your_key (optional)
```

### Railway Deployment
Add same variables in Railway dashboard under "Variables" tab.

## Customization

### Change Keywords
Edit `config.json`:
```json
{
  "keywords_core": [
    "AI trading analysis",
    "chart analyzer",
    "crypto analyzer"
  ]
}
```

### Adjust Scoring
Edit `main.py` → `_calculate_relevance_score()` method

### Customize UI
Edit `templates/index.html`

## Troubleshooting

### "Invalid Reddit credentials"
→ Check `.env` file for typos  
→ Ensure app type is "script" on Reddit  
→ No extra spaces or quotes

### "AI replies not working"
→ Check `ANTHROPIC_API_KEY` in `.env`  
→ App falls back to templates if no key  
→ Still fully functional!

### "No results found"
→ Select more keywords  
→ Increase date range  
→ Enable comment search

### "Port already in use"
→ Kill other process: `lsof -ti:5000 | xargs kill -9`  
→ Or use different port: `PORT=8000 python app.py`

## Next Steps

1. **Test Locally**: Run `python app.py` and test
2. **Deploy to Railway**: Follow RAILWAY_DEPLOY.md
3. **Customize**: Adjust keywords in config.json
4. **Use It**: Find leads and engage!

## Documentation

- **README.md** - Full documentation
- **RAILWAY_DEPLOY.md** - Railway deployment guide
- **V2_HIGHLIGHTS.md** - What's new in v2.0
- **config.json** - Keyword configuration

## Support

- **Issues**: GitHub issues
- **Questions**: Check README.md
- **Updates**: Watch the repo

## Pro Tips 💡

1. **Start with defaults** - Built-in keywords work great
2. **Test locally first** - Make sure it works before deploying
3. **Review AI replies** - Always read before posting
4. **Track results** - Note what gets engagement
5. **Be genuine** - Provide real value first

## Comparison: v1.0 vs v2.0

| Feature | v1.0 | v2.0 |
|---------|------|------|
| Interface | CLI | Web UI |
| Comments | ❌ | ✅ |
| AI Replies | ❌ | ✅ |
| Workflow | 10-15min | 2-3min |
| Deploy | GitHub Actions | Anywhere |

v2.0 is **5x faster** and **way easier** to use!

## Common Questions

**Q: Can I use both v1.0 and v2.0?**  
A: Yes! v1.0 for automation, v2.0 for interactive use.

**Q: Do I need Anthropic API key?**  
A: No, but recommended. Falls back to templates without it.

**Q: How much does Railway cost?**  
A: $5/month with $5 credit = typically $0-5/month.

**Q: Can I use my own AI model?**  
A: Yes! Edit `app.py` → `generate_reply()` function.

**Q: Is this better than v1.0?**  
A: For most users, yes! Much faster workflow.

## Success Checklist ✅

- [ ] Installed dependencies
- [ ] Got Reddit API credentials
- [ ] Created .env file
- [ ] Ran test_setup.py (all pass)
- [ ] Started app locally
- [ ] Performed a test scan
- [ ] Generated an AI reply
- [ ] (Optional) Deployed to Railway
- [ ] (Optional) Added Anthropic API key

## Ready to Go! 🚀

You now have everything you need to:
- Find high-quality Reddit opportunities
- Search both posts AND comments
- Generate AI-powered replies
- Deploy worldwide
- Scale your outreach

**Open the app and start your first scan!**

```bash
python app.py
```

Then visit: **http://localhost:5000**

---

**Questions?** Check README.md or open an issue.

**Happy lead hunting!** 🎯

*Built with ❤️ for TradingWizard.ai*
