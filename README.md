# Reddit Lead Finder v2.0 - Web Application 🚀

An intelligent web-based tool for finding and engaging with trading communities on Reddit. Built for TradingWizard.ai.

## 🆕 What's New in v2.0

### Major Features
- ✅ **Comment Search** - Now searches both posts AND comments
- ✅ **Web UI** - Beautiful, modern interface
- ✅ **AI Reply Generation** - Generate natural, helpful replies with Claude AI
- ✅ **Keyword Selection** - Choose which keywords to search
- ✅ **One-Click Actions** - Open posts, generate replies, copy text
- ✅ **Real-time Stats** - See posts/comments/scores at a glance
- ✅ **Railway Ready** - Deploy to Railway.com in minutes

### Enhanced Product Understanding
TradingWizard.ai features:
- AI-powered chart analysis for ANY stock, crypto, or forex symbol
- Just select a symbol and get instant technical analysis
- No need to upload charts - analyze any asset instantly
- Trading signals, market scans, and backtesting

## 🎯 Features

### Search Capabilities
- Search both **posts** and **comments**
- Multiple trading subreddits (algotrading, trading, daytrading, stocks, forex, crypto, etc.)
- Customizable keyword selection
- Adjustable date range (1-30 days)
- Smart relevance scoring (0-100)

### AI Reply Generation
- **Claude-powered** natural reply generation
- 50% helpful content + 50% soft pitch
- Respects subreddit rules (no links in restricted subs)
- One-click generation per post (prevents token waste)
- Fallback to templates if API key not provided

### User Interface
- Clean, modern design
- Keyword toggle selection
- Real-time statistics
- One-click copy to clipboard
- Direct links to Reddit posts/comments
- Mobile responsive

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/HugoRS00/reddit-lead-finder.git
   cd reddit-lead-finder
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your credentials
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open in browser**
   ```
   http://localhost:5000
   ```

### Railway Deployment

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Ready for Railway deployment"
   git push
   ```

2. **Deploy on Railway**
   - Go to [Railway.app](https://railway.app/)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway will auto-detect and deploy

3. **Add Environment Variables**
   In Railway dashboard, add these variables:
   - `REDDIT_CLIENT_ID` - Your Reddit app client ID
   - `REDDIT_CLIENT_SECRET` - Your Reddit app secret
   - `ANTHROPIC_API_KEY` - Your Anthropic API key (optional)
   - `REDDIT_USER_AGENT` - `TradingWizard Lead Finder v2.0`

4. **Done!** Your app is live!

### Alternative: Render.com Deployment

1. Go to [Render.com](https://render.com/)
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. Add environment variables
6. Deploy!

## 🔑 Getting API Keys

### Reddit API

1. Go to https://www.reddit.com/prefs/apps
2. Click "create another app..."
3. Fill in:
   - Name: `TradingWizard Lead Finder`
   - Type: **script**
   - Redirect URI: `http://localhost:8080`
4. Copy your `client_id` and `client_secret`

### Anthropic API (Optional)

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Go to "API Keys"
4. Create a new key
5. Copy your API key

**Note**: If you don't provide an Anthropic API key, the app will use template-based replies as a fallback.

## 📖 How to Use

### 1. Select Keywords
- Click on keyword tags to toggle selection
- Selected keywords are highlighted in purple
- Default keywords are optimized for TradingWizard.ai

### 2. Set Options
- Adjust date range (1-30 days)
- Toggle comment search on/off

### 3. Start Scan
- Click "🔍 Start Scan"
- Wait for results (usually 10-30 seconds)

### 4. Review Results
- See statistics: total leads, posts, comments, avg score
- Each lead shows:
  - Title and content
  - Relevance score
  - Intent label
  - Subreddit and metadata
  - Risk flags (if any)

### 5. Generate AI Reply
- Click "✨ Generate AI Reply" for any lead
- AI generates a helpful, natural reply
- Includes value-first content + soft pitch
- Respects subreddit rules

### 6. Copy and Post
- Click "📋 Copy Reply" to copy to clipboard
- Click "🔗 Open in Reddit" to visit the post
- Paste your reply and engage!

## 🎨 UI Features

### Keyword Selection
- Visual toggle system
- All keywords selected by default
- Easy to customize your search

### Lead Cards
- Color-coded relevance scores
- Type badges (post/comment)
- Intent labels (tool-seeking, how-to, etc.)
- Risk warnings

### AI Reply Section
- Expandable reply area
- Loading animation while generating
- One-click copy button

### Statistics Dashboard
- Total leads found
- Posts vs comments breakdown
- Average relevance score

## ⚙️ Configuration

### config.json

Customize your search:

```json
{
  "keywords_core": [
    "AI trading analysis",
    "chart analyzer",
    "crypto analyzer",
    "stock analyzer"
  ],
  "allowlist_subs": [],
  "blocklist_subs": ["politics", "memes"],
  "date_range_days": 7,
  "relevance_threshold": 60
}
```

### Scoring System

Leads are scored 0-100 based on:
- **Intent Match (40%)** - Tool-seeking, how-to, problem-solving
- **Keyword Density (20%)** - Number of matched keywords
- **Context Fit (25%)** - Relevance to TradingWizard features
- **Freshness (10%)** - How recent the post/comment is
- **Subreddit Quality (5%)** - Quality/relevance of subreddit

### Reply Generation

AI replies follow this structure:
1. **Value First (50%)** - Concrete trading tips, actionable advice
2. **Soft Pitch (50%)** - Natural mention of TradingWizard.ai
3. **Disclosure** - Light disclosure when appropriate
4. **No Hype** - Conversational, not salesy

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: Vanilla JS + CSS
- **Reddit API**: PRAW library
- **AI**: Anthropic Claude API
- **Deployment**: Railway / Render / Heroku compatible

## 📊 API Endpoints

### POST /api/scan
Scan Reddit for leads
```json
{
  "keywords": ["AI trading", "chart analyzer"],
  "date_range": 7,
  "search_comments": true
}
```

### POST /api/generate-reply
Generate AI reply for a lead
```json
{
  "context": "Post/comment content",
  "intent_label": "Tool-seeking",
  "include_link": true,
  "type": "post"
}
```

### GET /api/default-keywords
Get default keywords from config

### GET /health
Health check endpoint

## 🔒 Security & Privacy

- Environment variables for all API keys
- No data persistence (searches happen in real-time)
- No user data collection
- Rate limiting respected
- Subreddit rules honored

## 📝 Best Practices

### Search Strategy
1. Start with default keywords
2. Test different date ranges
3. Enable comment search for more opportunities
4. Focus on leads with score 70+

### Reply Strategy
1. Always review AI-generated replies
2. Customize to match your voice
3. Add personal touch before posting
4. Engage with follow-up comments
5. Track what works

### Deployment Tips
1. Use environment variables for secrets
2. Monitor Railway logs for errors
3. Set up health check monitoring
4. Consider adding caching for large scans

## 🚨 Troubleshooting

### "Invalid Reddit credentials"
- Check your `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET`
- Ensure no extra spaces or quotes
- Verify app type is "script" on Reddit

### "AI reply generation failed"
- Check your `ANTHROPIC_API_KEY`
- Verify API key is active
- App will fall back to templates if API fails

### "No results found"
- Try broader keywords
- Lower relevance threshold in config
- Increase date range
- Check if subreddits are active

### Railway deployment issues
- Ensure all environment variables are set
- Check Railway logs for errors
- Verify `Procfile` and `requirements.txt` are correct

## 🎯 Roadmap

- [ ] Save/export results to CSV
- [ ] Custom subreddit selection in UI
- [ ] Reply history tracking
- [ ] A/B testing for reply variants
- [ ] Slack/Discord notifications
- [ ] CRM integration (HubSpot, Salesforce)
- [ ] Analytics dashboard
- [ ] Scheduled scans

## 🤝 Contributing

Contributions welcome! This is a v2.0 rewrite with major improvements. Areas for contribution:
- Additional AI models support
- More reply templates
- Enhanced scoring algorithm
- Better UI/UX
- Performance optimizations

## 📄 License

MIT License - See LICENSE file

## 💡 Tips for Success

1. **Be Genuine**: Provide real value in every reply
2. **Respect Communities**: Follow subreddit rules
3. **Build Relationships**: Engage beyond just marketing
4. **Track Results**: Monitor what generates conversations
5. **Iterate**: Refine your approach based on data

## 🌟 Support

- **Issues**: Open an issue on GitHub
- **Questions**: Check the documentation
- **Improvements**: Submit a pull request

---

**Built with ❤️ for TradingWizard.ai**

Happy lead hunting! 🎯
