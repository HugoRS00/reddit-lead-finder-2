# 🚀 QUICK DEPLOY GUIDE

## ✅ What You Need to Do

### 1. Copy These Files to Your Repo:

**NEW FILES:**
- `app.py` (root folder)
- `templates/index.html` (create `templates` folder first!)
- `Procfile` (root folder)

**UPDATE THESE:**
- `requirements.txt` - Replace content
- `.gitignore` - Add database lines at end

**DON'T TOUCH:**
- `main.py` (unchanged)
- `config.json` (unchanged)
- All other files (unchanged)

### 2. Push to GitHub:
```bash
git add .
git commit -m "Add web dashboard v2.0"
git push origin main
```

### 3. Railway Will Auto-Deploy!

Wait 1-2 minutes, then visit your Railway URL.

## 🎯 How to Use Dashboard

1. Click **"🔍 Scan Reddit"**
2. Wait 30-60 seconds
3. Review leads (sorted by score)
4. For each lead:
   - Choose reply mode (Ghost/Soft/Full)
   - Adjust tone slider (Casual ↔ Professional)
   - Choose length (Short/Medium/Long)
   - Click **"🔄 Generate"** for 3 variants
   - Edit reply in textarea
   - Click **"📋 Copy"** to copy
   - Click **"🛡️ Check Spam"** to verify
5. Mark status (New/Saved/Replied/Skipped)

## ✨ New Features You Got:

1. 🌙 **Dark Mode** - Toggle button in header
2. 🎭 **Reply Modes:**
   - **Ghost** = Pure value, no TradingWizard mention
   - **Soft** = Mention "TradingWizard AI" (no link)
   - **Full** = Mention "TradingWizard.ai" with link
3. 💾 **Save for Later** - Track: New/Saved/Replied/Skipped
4. 🔍 **Smart Filters** - Filter by status
5. 📊 **Dashboard** - See stats at top
6. ✏️ **Inline Editing** - Edit replies before copying
7. 🎯 **3 Variants** - Get A/B/C options
8. 🎚️ **Tone Control** - Casual to Professional
9. 📏 **Reply Length** - Short/Medium/Long
10. 🛡️ **Spam Checker** - Safety score
11. ⚠️ **Subreddit Rules** - Auto-check

## 🎉 Done!

Your Reddit Lead Finder now has a professional web interface!

---

Questions? Everything still works exactly like before, just with a web UI now!