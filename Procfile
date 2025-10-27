web: gunicorn app:app
```

That's it! Just one line. This tells Railway how to run your web app.

---

## 📄 FILE 5: `.gitignore` (UPDATE)

You already have a `.gitignore` file. **Add these lines at the very bottom** of your existing file:
```
# Database
leads.db
*.db
*.sqlite
*.sqlite3
```

So your complete `.gitignore` should look like this:
```
# Environment variables
.env
.env.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Project specific
leads.json
*.log

# Database  ← ADD THESE 4 LINES
leads.db
*.db
*.sqlite
*.sqlite3
```

---

## 📂 Final File Structure

After adding everything, your repo should look like:
```
reddit-lead-finder/
├── app.py                  ← NEW
├── Procfile                ← NEW
├── requirements.txt        ← UPDATED
├── .gitignore              ← UPDATED (added 4 lines)
├── templates/              ← NEW FOLDER
│   └── index.html          ← NEW
├── main.py                 ← unchanged
├── config.json             ← unchanged
├── .env.example            ← unchanged
├── README.md               ← unchanged
└── ... (all other files unchanged)