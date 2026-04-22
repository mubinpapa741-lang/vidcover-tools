# VidCover Tools — Project Context

## 🔗 Quick Links
- **GitHub:** https://github.com/mubinpapa741-lang/vidcover-tools
- **Deploy:** Render.com (auto-deploys from `master` branch)
- **Admin:** `/dashboard` (Password: `vidcover2026`)
- **Local:** `python app.py` → http://localhost:5050

## 📁 Key Files
| File | Purpose |
|------|---------|
| `app.py` | Main Flask app — voice generation, API routes, VOICE_MAP |
| `database.py` | SQLite DB — plans, activation codes, usage tracking |
| `templates/promo.html` | Sales/promo page with free trial voice cards |
| `templates/tools.html` | VoiceCover generation page (main tool) |
| `templates/dashboard.html` | Admin dashboard |
| `static/css/style.css` | Full site styling (3400+ lines) |
| `requirements.txt` | Python dependencies |

## 🎙️ Voice Configuration (VOICE_MAP in app.py)
| Language | Female Voice | Male Voice |
|----------|-------------|------------|
| Bangla | `bn-IN-TanishaaNeural` | `bn-BD-PradeepNeural` |
| English US | `en-US-AvaNeural` | `en-US-AndrewNeural` |
| English UK | `en-GB-LibbyNeural` | `en-GB-ThomasNeural` |
| English AU | `en-AU-NatashaNeural` | `en-AU-WilliamNeural` |
| English IN | `en-IN-NeerjaNeural` | `en-IN-PrabhatNeural` |
| Hindi | `hi-IN-SwaraNeural` | `en-US-BrianMultilingualNeural` |

## ✅ Features Completed
1. **Neural TTS** — Microsoft edge-tts with best voices per language
2. **SSML Support** — Natural pauses, prosody control
3. **Duo Mix** — 50% Male + 50% Female combined voiceover (👫 button)
4. **Word Counting** — Unicode-safe, handles Bangla zero-width chars
5. **Case-Insensitive Activation** — Codes work regardless of case
6. **Trial Voices** — Free voice preview on promo page (no download button)
7. **Speed Control** — Slow (-18%), Normal (-12%), Fast (+8%)
8. **Subscription Plans** — Starter/Business/Agency with daily limits
9. **PWA Support** — Installable as app on mobile/desktop

## 🔧 Tech Stack
- **Backend:** Python 3.14, Flask, edge-tts, SQLite
- **Frontend:** Vanilla HTML/CSS/JS (no frameworks)
- **Deploy:** Render.com (free tier, auto-deploy from GitHub)
- **TTS Engine:** Microsoft Edge Neural TTS (free, no API key needed)

## 📝 How to Deploy Changes
```bash
git add .
git commit -m "description of changes"
git push origin master
# Render auto-deploys in 2-3 minutes
```

## ⚠️ Known Limitations
- edge-tts has quality ceiling — Bangla/Hindi not as good as English
- For premium quality, upgrade to Azure Speech API (free 500K chars/month)
- MP3 concatenation (Duo Mix) uses binary concat — works but no silence gap
