"""
🎬 VidCover Tools — Main Application
Flask-based subscription management app with real-time admin dashboard.
Supports Mobile, PC, Laptop — fully responsive.
"""

import os
import sys
import socket
import uuid
import io
import re
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, session
from functools import wraps

# PyInstaller bundled EXE support
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_DIR)

import database as db

app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(32).hex())

# Secure session cookies
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# ============================================================================
# ADMIN CONFIG — Password protected (use env var or default)
# ============================================================================
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "vidcover2026")


def admin_required(f):
    """Decorator: protect routes so only admin can access."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('is_admin'):
            if request.is_json:
                return jsonify({"success": False, "error": "Admin access required!"}), 403
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated


# ============================================================================
# PAGE ROUTES (Client-facing — no login needed)
# ============================================================================

@app.route("/")
def index():
    """Landing page with plan overview."""
    active_plans = db.get_active_plans()
    stats = db.get_dashboard_stats()
    return render_template("index.html", plans=db.PLANS, active_plans=active_plans, stats=stats)


@app.route("/activate")
def activate_page():
    """Plan activation page."""
    return render_template("activate.html", plans=db.PLANS)


# ============================================================================
# ADMIN ROUTES (Password protected — only you can access)
# ============================================================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Admin login page."""
    error = None
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect(url_for('dashboard'))
        else:
            error = "❌ Wrong password!"
    return render_template("admin_login.html", error=error)


@app.route("/admin/logout")
def admin_logout():
    """Admin logout."""
    session.pop('is_admin', None)
    return redirect(url_for('index'))


@app.route("/dashboard")
@admin_required
def dashboard():
    """Admin dashboard — real-time plan management. PASSWORD PROTECTED."""
    active_plans = db.get_active_plans()
    all_plans = db.get_all_plans()
    expired_plans = db.get_expired_plans()
    stats = db.get_dashboard_stats()
    codes = db.get_all_codes()
    promo_link = db.get_promo_link()
    return render_template("dashboard.html",
                           active_plans=active_plans,
                           all_plans=all_plans,
                           expired_plans=expired_plans,
                           stats=stats,
                           codes=codes,
                           plans_info=db.PLANS,
                           promo_link=promo_link)


@app.route("/promo")
def promo_page():
    """Ad landing page — share this link in ads."""
    promo_link = db.get_promo_link()
    return render_template("promo.html", promo_link=promo_link)


@app.route("/tools")
def tools_page():
    """VidCover tools page — requires active plan."""
    active_plans = db.get_active_plans()
    daily_used = 0
    plan_limits = {}
    if active_plans:
        plan = active_plans[0]
        daily_used = db.get_daily_usage(plan["id"])
        plan_limits = db.PLANS.get(plan["plan_tier"], {})
    return render_template("tools.html",
                           active_plans=active_plans,
                           plans_info=db.PLANS,
                           daily_used=daily_used,
                           plan_limits=plan_limits)


# ============================================================================
# VOICEOVER TOOL API — Microsoft Neural Voices (Professional Quality)
# ============================================================================

import asyncio
import edge_tts

# Create output folder for generated audio files
OUTPUT_DIR = os.path.join(BASE_DIR, 'data', 'audio')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Professional Neural Voice Map — BEST of all tests applied
# Mix of dedicated + multilingual voices — each picked for BEST quality per language
VOICE_MAP = {
    # Bangla Female — Bangladesh Nabanita = authentic Bangladeshi tone, natural & smooth
    'bn-female': {'voice': 'bn-BD-NabanitaNeural',             'lang': 'Bangla', 'gender': 'Female', 'flag': '🇧🇩'},
    # Bangla Male — Bangladesh Pradeep = authentic Bangla pronunciation
    'bn-male':   {'voice': 'bn-BD-PradeepNeural',             'lang': 'Bangla', 'gender': 'Male',   'flag': '🇧🇩'},
    # English US — Latest gen voices (already best)
    'en-male':   {'voice': 'en-US-AndrewNeural',     'lang': 'English (US)', 'gender': 'Male',   'flag': '🇺🇸'},
    'en-female': {'voice': 'en-US-AvaNeural',         'lang': 'English (US)', 'gender': 'Female', 'flag': '🇺🇸'},
    # English UK
    'en-uk-male':   {'voice': 'en-GB-ThomasNeural',  'lang': 'English (UK)', 'gender': 'Male',   'flag': '🇬🇧'},
    'en-uk-female': {'voice': 'en-GB-LibbyNeural',    'lang': 'English (UK)', 'gender': 'Female', 'flag': '🇬🇧'},
    # English Australia
    'en-au-male':   {'voice': 'en-AU-WilliamNeural', 'lang': 'English (AU)', 'gender': 'Male',   'flag': '🇦🇺'},
    'en-au-female': {'voice': 'en-AU-NatashaNeural', 'lang': 'English (AU)', 'gender': 'Female', 'flag': '🇦🇺'},
    # English India
    'en-in-male':   {'voice': 'en-IN-PrabhatNeural', 'lang': 'English (India)', 'gender': 'Male',   'flag': '🇮🇳'},
    'en-in-female': {'voice': 'en-IN-NeerjaNeural',  'lang': 'English (India)', 'gender': 'Female', 'flag': '🇮🇳'},
    # Hindi Female — Dedicated Swara = best pronunciation + natural tone (78KB)
    'hi-female': {'voice': 'hi-IN-SwaraNeural',               'lang': 'Hindi', 'gender': 'Female', 'flag': '🇮🇳'},
    # Hindi Male — Multilingual Brian = richer, more natural male Hindi
    'hi-male':   {'voice': 'en-US-BrianMultilingualNeural',   'lang': 'Hindi', 'gender': 'Male',   'flag': '🇮🇳'},
}


def _count_words(text):
    """Properly count words for both Bangla and English text."""
    # Remove zero-width characters and normalize whitespace
    cleaned = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)
    cleaned = cleaned.strip()
    if not cleaned:
        return 0
    # Split by whitespace (works for Bangla, English, Hindi)
    words = re.split(r'\s+', cleaned)
    return len(words)


def _prepare_text(text, voice_key):
    """Preprocess text for better pronunciation across all languages."""
    processed = text.strip()
    
    # === BANGLA SPECIFIC FIXES ===
    if voice_key.startswith('bn') or voice_key == 'bn-mixed':
        # Fix common Bangla number pronunciation
        bn_digits = {'0': 'শূন্য', '1': 'এক', '2': 'দুই', '3': 'তিন', '4': 'চার', '5': 'পাঁচ', 
                     '6': 'ছয়', '7': 'সাত', '8': 'আট', '9': 'নয়'}
        # Convert standalone digits to Bangla words
        def replace_number(match):
            num = match.group(0)
            if len(num) <= 4:  # Only convert small numbers
                return ' '.join(bn_digits.get(d, d) for d in num)
            return num
        processed = re.sub(r'\b\d{1,4}\b', replace_number, processed)
        
        # Fix percentage signs
        processed = processed.replace('%', ' পারসেন্ট')
        
        # Add natural pauses around dashes and colons in Bangla
        processed = re.sub(r'\s*[\u2014\u2013-]\s*', ', ', processed)
        
    # === HINDI SPECIFIC FIXES ===  
    elif voice_key.startswith('hi'):
        processed = processed.replace('%', ' प्रतिशत')
        processed = re.sub(r'\s*[\u2014\u2013-]\s*', ', ', processed)
    
    # === ALL LANGUAGES: General fixes ===
    # Remove excessive spaces
    processed = re.sub(r'\s{2,}', ' ', processed)
    # Ensure proper sentence endings have spaces
    processed = re.sub(r'([।.!?])([^\s])', r'\1 \2', processed)
    # Remove zero-width chars that mess up pronunciation
    processed = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', processed)
    
    return processed.strip()


async def _generate_tts(text, voice_name, rate, filepath, voice_key=''):
    """Async helper to generate TTS with edge-tts."""
    # Preprocess text for better pronunciation
    clean_text = _prepare_text(text, voice_key)
    
    communicate = edge_tts.Communicate(text=clean_text, voice=voice_name, rate=rate)
    await communicate.save(filepath)


def _split_text_for_duo(text):
    """Split text into two roughly equal halves by sentences for Duo voice."""
    # Split by sentence boundaries (Bangla ।, English .!?)
    sentences = re.split(r'(?<=[।\.\!\?])\s*', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) < 2:
        # If single sentence, split by words at midpoint
        words = text.strip().split()
        mid = len(words) // 2
        part1 = ' '.join(words[:mid])
        part2 = ' '.join(words[mid:])
        return part1, part2
    
    # Find midpoint by total character count
    total_chars = sum(len(s) for s in sentences)
    mid_target = total_chars // 2
    
    running = 0
    split_idx = 0
    for i, s in enumerate(sentences):
        running += len(s)
        if running >= mid_target:
            split_idx = i + 1
            break
    
    if split_idx == 0:
        split_idx = 1
    if split_idx >= len(sentences):
        split_idx = len(sentences) - 1
    
    part1 = ' '.join(sentences[:split_idx])
    part2 = ' '.join(sentences[split_idx:])
    return part1, part2


def _merge_audio_files(file1, file2, output_path):
    """Merge two MP3 files into one. MP3 is frame-based so simple concatenation works."""
    with open(output_path, 'wb') as out:
        with open(file1, 'rb') as f1:
            out.write(f1.read())
        with open(file2, 'rb') as f2:
            out.write(f2.read())
    return output_path


@app.route("/api/voiceover", methods=["POST"])
def api_generate_voiceover():
    """Generate a professional neural voiceover. Requires an active plan with limits."""
    # Check if user has active plan
    active_plans = db.get_active_plans()
    if not active_plans:
        return jsonify({"success": False, "error": "No active plan! Activate a plan first."}), 403

    # Get current plan info
    plan = active_plans[0]
    plan_tier = plan["plan_tier"]
    plan_info = db.PLANS[plan_tier]
    plan_id = plan["id"]

    # Check daily usage limit
    daily_used = db.get_daily_usage(plan_id)
    daily_limit = plan_info["daily_limit"]
    if daily_used >= daily_limit:
        return jsonify({
            "success": False,
            "error": f"Daily limit reached! ({daily_used}/{daily_limit} videos today). Upgrade your plan for more."
        }), 429

    data = request.get_json() or {}
    text = data.get("text", "").strip()
    voice_key = data.get("voice", "bn-female")
    speed = data.get("speed", "normal")

    if not text:
        return jsonify({"success": False, "error": "Please enter some text!"}), 400

    # Check word count limit (proper Bangla/Unicode counting)
    word_count = _count_words(text)
    max_words = plan_info["max_words"]
    if word_count > max_words:
        return jsonify({
            "success": False,
            "error": f"Too many words! Your {plan_info['name']} plan allows max {max_words} words. You typed {word_count} words."
        }), 400

    # Check voice access for Starter plan
    allowed_voices = plan_info["voices"]
    if allowed_voices != "all":
        if voice_key.endswith('-mixed'):
            # For mixed, check both male and female are accessible
            lang_prefix = voice_key.replace('-mixed', '')
            if f"{lang_prefix}-male" not in allowed_voices or f"{lang_prefix}-female" not in allowed_voices:
                return jsonify({
                    "success": False,
                    "error": f"Duo Mix voice not available on {plan_info['name']} plan! Upgrade to Business or Agency."
                }), 403
        elif voice_key not in allowed_voices:
            return jsonify({
                "success": False,
                "error": f"This voice is not available on {plan_info['name']} plan! Upgrade to Business or Agency for all voices."
            }), 403

    # Get voice config
    voice_info = VOICE_MAP.get(voice_key, VOICE_MAP['bn-female'])

    # Speed mapping — tuned for most natural human-like sound
    rate_map = {'slow': '-15%', 'normal': '-6%', 'fast': '+10%'}
    rate = rate_map.get(speed, '-6%')

    try:
        filename = f"voiceover_{uuid.uuid4().hex[:8]}.mp3"
        filepath = os.path.join(OUTPUT_DIR, filename)

        # Check if this is a MIXED/DUO voice request
        if voice_key.endswith('-mixed'):
            # Mixed mode: 50% male + 50% female
            lang_prefix = voice_key.replace('-mixed', '')  # e.g., 'bn', 'en', 'hi'
            male_key = f"{lang_prefix}-male"
            female_key = f"{lang_prefix}-female"
            
            male_voice = VOICE_MAP.get(male_key, VOICE_MAP['bn-male'])
            female_voice = VOICE_MAP.get(female_key, VOICE_MAP['bn-female'])
            
            # Split text 50/50
            part1, part2 = _split_text_for_duo(text)
            
            # Generate both parts in single async context
            male_file = os.path.join(OUTPUT_DIR, f"duo_male_{uuid.uuid4().hex[:6]}.mp3")
            female_file = os.path.join(OUTPUT_DIR, f"duo_female_{uuid.uuid4().hex[:6]}.mp3")
            
            async def _gen_duo():
                await _generate_tts(part1, male_voice['voice'], rate, male_file, voice_key=male_key)
                await _generate_tts(part2, female_voice['voice'], rate, female_file, voice_key=female_key)
            
            asyncio.run(_gen_duo())
            
            # Merge both into one
            _merge_audio_files(male_file, female_file, filepath)
            
            # Clean up temp files
            try:
                os.remove(male_file)
                os.remove(female_file)
            except:
                pass
            
            gender_label = "Mixed (Male + Female)"
            lang_label = male_voice['lang']
        else:
            # Standard single voice generation
            asyncio.run(_generate_tts(text, voice_info['voice'], rate, filepath, voice_key=voice_key))
            gender_label = voice_info['gender']
            lang_label = voice_info['lang']

        # Increment daily usage
        db.increment_daily_usage(plan_id)
        daily_used += 1

        return jsonify({
            "success": True,
            "message": f"✅ {gender_label} VoiceCover generated in {lang_label}!",
            "filename": filename,
            "download_url": f"/api/voiceover/download/{filename}",
            "language": lang_label,
            "gender": gender_label,
            "text_length": len(text),
            "word_count": word_count,
            "daily_used": daily_used,
            "daily_limit": daily_limit
        })
    except Exception as e:
        return jsonify({"success": False, "error": f"Generation failed: {str(e)}"}), 500


@app.route("/api/voiceover/download/<filename>")
def api_download_voiceover(filename):
    """Download a generated voiceover file."""
    # Security: prevent path traversal attacks
    if '..' in filename or '/' in filename or '\\' in filename:
        return jsonify({"success": False, "error": "Invalid filename!"}), 400
    filepath = os.path.join(OUTPUT_DIR, filename)
    # Verify file is inside OUTPUT_DIR
    if not os.path.abspath(filepath).startswith(os.path.abspath(OUTPUT_DIR)):
        return jsonify({"success": False, "error": "Access denied!"}), 403
    if not os.path.exists(filepath):
        return jsonify({"success": False, "error": "File not found!"}), 404
    return send_file(filepath, mimetype='audio/mpeg', as_attachment=True, download_name=filename)


# ============================================================================
# TRIAL / DEMO API — Fixed demo text, listen only, no plan needed
# ============================================================================

TRIAL_TEXTS = {
    'bn': "আজকের ভিডিওতে আমি দেখাব কিভাবে মাত্র কয়েক মিনিটে প্রফেশনাল ভয়েসকভার তৈরি করা যায়। চলুন শুরু করি!",
    'en': "Welcome to today's video! I'll show you how to create stunning professional voiceovers in just minutes. Let's get started right now!",
    'hi': "नमस्ते दोस्तों! आज के वीडियो में मैं आपको दिखाऊंगा कि कैसे कुछ ही मिनटों में प्रोफेशनल वॉयसओवर बनाया जाता है।",
}

# Map voice keys to their language for trial text
TRIAL_LANG_MAP = {
    'bn-male': 'bn', 'bn-female': 'bn', 'bn-mixed': 'bn',
    'en-male': 'en', 'en-female': 'en', 'en-mixed': 'en',
    'en-uk-male': 'en', 'en-uk-female': 'en', 'en-uk-mixed': 'en',
    'en-au-male': 'en', 'en-au-female': 'en', 'en-au-mixed': 'en',
    'en-in-male': 'en', 'en-in-female': 'en', 'en-in-mixed': 'en',
    'hi-male': 'hi', 'hi-female': 'hi', 'hi-mixed': 'hi',
}

TRIAL_DIR = os.path.join(BASE_DIR, 'data', 'trial')
os.makedirs(TRIAL_DIR, exist_ok=True)


@app.route("/api/trial", methods=["POST"])
def api_trial_voice():
    """Generate a trial voiceover from FIXED demo text. No plan needed. Listen only."""
    data = request.get_json() or {}
    voice_key = data.get("voice", "bn-female")

    # Check if it's a valid voice key (single or mixed)
    is_mixed = voice_key.endswith('-mixed')
    if not is_mixed and voice_key not in VOICE_MAP:
        return jsonify({"success": False, "error": "Invalid voice!"}), 400
    if is_mixed:
        lang_prefix = voice_key.replace('-mixed', '')
        if f"{lang_prefix}-male" not in VOICE_MAP or f"{lang_prefix}-female" not in VOICE_MAP:
            return jsonify({"success": False, "error": "Invalid mixed voice!"}), 400

    lang_key = TRIAL_LANG_MAP.get(voice_key, 'en')
    demo_text = TRIAL_TEXTS[lang_key]

    # Use cached file if exists (avoid regenerating same demo)
    cache_file = os.path.join(TRIAL_DIR, f"trial_{voice_key}.mp3")
    if not os.path.exists(cache_file):
        try:
            if is_mixed:
                # Duo Mix: split text 50/50, male first then female
                lang_prefix = voice_key.replace('-mixed', '')
                male_voice = VOICE_MAP[f"{lang_prefix}-male"]
                female_voice = VOICE_MAP[f"{lang_prefix}-female"]
                part1, part2 = _split_text_for_duo(demo_text)

                male_tmp = os.path.join(TRIAL_DIR, f"trial_{voice_key}_male_tmp.mp3")
                female_tmp = os.path.join(TRIAL_DIR, f"trial_{voice_key}_female_tmp.mp3")

                async def _gen_trial_duo():
                    await _generate_tts(part1, male_voice['voice'], '-6%', male_tmp, voice_key=f"{lang_prefix}-male")
                    await _generate_tts(part2, female_voice['voice'], '-6%', female_tmp, voice_key=f"{lang_prefix}-female")

                asyncio.run(_gen_trial_duo())
                _merge_audio_files(male_tmp, female_tmp, cache_file)

                # Cleanup temp files
                try:
                    os.remove(male_tmp)
                    os.remove(female_tmp)
                except:
                    pass
            else:
                voice_info = VOICE_MAP[voice_key]
                asyncio.run(_generate_tts(demo_text, voice_info['voice'], '-6%', cache_file, voice_key=voice_key))
        except Exception as e:
            return jsonify({"success": False, "error": f"Trial generation failed: {str(e)}"}), 500

    # Build response label
    if is_mixed:
        lang_prefix = voice_key.replace('-mixed', '')
        lang_label = VOICE_MAP[f"{lang_prefix}-male"]['lang']
        return jsonify({
            "success": True,
            "message": f"🎧 👫 Duo Mix — {lang_label}",
            "play_url": f"/api/trial/play/{voice_key}",
            "language": lang_label,
            "gender": "Mixed (Male + Female)",
        })
    else:
        voice_info = VOICE_MAP[voice_key]
        return jsonify({
            "success": True,
            "message": f"🎧 {voice_info['gender']} {voice_info['lang']} Trial",
            "play_url": f"/api/trial/play/{voice_key}",
            "language": voice_info['lang'],
            "gender": voice_info['gender'],
        })


@app.route("/api/trial/play/<voice_key>")
def api_trial_play(voice_key):
    """Stream trial audio for playback. No download headers."""
    if '..' in voice_key or '/' in voice_key or '\\' in voice_key:
        return jsonify({"success": False, "error": "Invalid!"}), 400
    # Allow mixed voice keys like 'bn-mixed', 'en-mixed' etc.
    safe_key = voice_key.replace('-', '_').replace('.', '')
    cache_file = os.path.join(TRIAL_DIR, f"trial_{voice_key}.mp3")
    if not os.path.exists(cache_file):
        return jsonify({"success": False, "error": "Trial not generated yet!"}), 404
    # Stream for playback only — no as_attachment (prevents easy download)
    response = send_file(cache_file, mimetype='audio/mpeg', as_attachment=False)
    response.headers['Cache-Control'] = 'public, max-age=86400'
    return response



# ============================================================================
# PWA ROUTES (Service Worker & Manifest from root scope)
# ============================================================================

@app.route("/sw.js")
def service_worker():
    """Serve service worker from root scope for PWA."""
    response = send_file(
        os.path.join(BASE_DIR, 'static', 'sw.js'),
        mimetype='application/javascript'
    )
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Cache-Control'] = 'no-cache'
    return response


@app.route("/manifest.json")
def manifest():
    """Serve PWA manifest from root."""
    return send_file(
        os.path.join(BASE_DIR, 'static', 'manifest.json'),
        mimetype='application/json'
    )


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route("/api/activate", methods=["POST"])
def api_activate():
    """Activate a plan with a code."""
    data = request.get_json() or {}
    code = data.get("code", "").strip()
    label = data.get("label", "").strip()

    if not code:
        return jsonify({"success": False, "error": "Please enter an activation code!"}), 400

    result = db.activate_plan(code, label)
    status = 200 if result["success"] else 400
    return jsonify(result), status


@app.route("/api/plans", methods=["GET"])
@admin_required
def api_get_plans():
    """Get all plans. ADMIN ONLY."""
    filter_type = request.args.get("filter", "active")
    if filter_type == "all":
        plans = db.get_all_plans()
    elif filter_type == "expired":
        plans = db.get_expired_plans()
    else:
        plans = db.get_active_plans()
    return jsonify({"plans": plans, "count": len(plans)})


@app.route("/api/plans/<int:plan_id>", methods=["DELETE"])
@admin_required
def api_delete_plan(plan_id):
    """Delete a plan. ADMIN ONLY."""
    result = db.delete_plan(plan_id)
    return jsonify(result)


@app.route("/api/plans/<int:plan_id>/deactivate", methods=["POST"])
@admin_required
def api_deactivate_plan(plan_id):
    """Deactivate a plan. ADMIN ONLY."""
    result = db.deactivate_plan(plan_id)
    return jsonify(result)


@app.route("/api/cleanup", methods=["POST"])
@admin_required
def api_cleanup():
    """Delete all expired plans. ADMIN ONLY."""
    result = db.cleanup_expired()
    return jsonify(result)


@app.route("/api/stats", methods=["GET"])
@admin_required
def api_stats():
    """Get dashboard statistics. ADMIN ONLY."""
    stats = db.get_dashboard_stats()
    return jsonify(stats)


@app.route("/api/codes", methods=["GET"])
@admin_required
def api_get_codes():
    """Get all activation codes. ADMIN ONLY."""
    codes = db.get_all_codes()
    return jsonify({"codes": codes, "count": len(codes)})


@app.route("/api/codes/create", methods=["POST"])
@admin_required
def api_create_code():
    """Create a new activation code. ADMIN ONLY."""
    data = request.get_json() or {}
    code = data.get("code", "").strip()
    plan_tier = data.get("plan_tier", 0)

    if not code:
        return jsonify({"success": False, "error": "Code cannot be empty!"}), 400

    try:
        plan_tier = int(plan_tier)
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid plan tier!"}), 400

    result = db.create_code(code, plan_tier)
    status = 200 if result["success"] else 400
    return jsonify(result), status


@app.route("/api/codes/<int:code_id>", methods=["DELETE"])
@admin_required
def api_delete_code(code_id):
    """Delete an activation code. ADMIN ONLY."""
    result = db.delete_code(code_id)
    return jsonify(result)


# ============================================================================
# PROMO LINK API
# ============================================================================

@app.route("/api/promo-link", methods=["GET"])
@admin_required
def api_get_promo_link():
    """Get the saved promo link. ADMIN ONLY."""
    link = db.get_promo_link()
    return jsonify({"success": True, "promo_link": link})


@app.route("/api/promo-link", methods=["POST"])
@admin_required
def api_set_promo_link():
    """Save/update the promo link. ADMIN ONLY."""
    data = request.get_json() or {}
    link = data.get("promo_link", "").strip()

    if not link:
        return jsonify({"success": False, "error": "Promo link cannot be empty!"}), 400

    result = db.set_promo_link(link)
    status = 200 if result["success"] else 400
    return jsonify(result), status


@app.route("/api/promo-link", methods=["DELETE"])
@admin_required
def api_delete_promo_link():
    """Delete the saved promo link. ADMIN ONLY."""
    db.set_setting("promo_link", "")
    return jsonify({"success": True, "message": "Promo link removed!"})


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    def get_lan_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "unknown"

    lan_ip = get_lan_ip()
    stats = db.get_dashboard_stats()

    print("\n" + "=" * 60)
    print("  🎬 VIDCOVER TOOLS")
    print("  Subscription Management Dashboard")
    print("=" * 60)
    print(f"\n  🖥️  This PC:       http://localhost:5050")
    print(f"  📱  Mobile/Other:  http://{lan_ip}:5050")
    print(f"  📊  Dashboard:     http://localhost:5050/dashboard")
    print(f"  🔑  Activate:      http://localhost:5050/activate")
    print(f"\n  Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Active Plans: {stats['active_plans']}")
    print(f"  Available Codes: {stats['available_codes']}")
    print("=" * 60 + "\n")

    app.run(debug=False, host="0.0.0.0", port=5050)
