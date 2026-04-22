"""
🎬 VidCover Tools — Database Manager
SQLite-based database for managing subscription plans and activation codes.
"""

import os
import sqlite3
from datetime import datetime, timedelta

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "vidcover.db")

# Plan definitions with pricing and limits
PLANS = {
    1: {
        "name": "Starter", "emoji": "⚡", "color": "#06b6d4",
        "gradient": "linear-gradient(135deg, #0e7490, #06b6d4)",
        "price": "199", "currency": "৳",
        "max_words": 250, "daily_limit": 10,
        "voices": ["bn-male", "bn-female", "en-male", "en-female"],
        "voice_label": "Bangla & English Only",
    },
    2: {
        "name": "Business", "emoji": "🔥", "color": "#8b5cf6",
        "gradient": "linear-gradient(135deg, #6d28d9, #a78bfa)",
        "price": "499", "currency": "৳",
        "max_words": 1050, "daily_limit": 25,
        "voices": "all",
        "voice_label": "All Voices Unlocked",
    },
    3: {
        "name": "Agency", "emoji": "💎", "color": "#f59e0b",
        "gradient": "linear-gradient(135deg, #d97706, #fbbf24)",
        "price": "1499", "currency": "৳",
        "max_words": 2500, "daily_limit": 100,
        "voices": "all",
        "voice_label": "All Voices Unlocked",
    },
}


def get_db():
    """Get database connection."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Initialize database tables."""
    conn = get_db()
    cursor = conn.cursor()

    # Activation codes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activation_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            plan_tier INTEGER NOT NULL CHECK(plan_tier IN (1, 2, 3)),
            is_used INTEGER DEFAULT 0,
            used_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Active plans table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS active_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_tier INTEGER NOT NULL CHECK(plan_tier IN (1, 2, 3)),
            plan_name TEXT NOT NULL,
            activation_code TEXT NOT NULL,
            user_label TEXT DEFAULT '',
            activated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Plan activation history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_tier INTEGER NOT NULL,
            plan_name TEXT NOT NULL,
            activation_code TEXT NOT NULL,
            action TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Daily usage tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            usage_count INTEGER DEFAULT 0,
            UNIQUE(plan_id, date)
        )
    """)

    # Settings table (for promo link, etc.)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# ============================================================================
# SETTINGS (Promo Link, etc.)
# ============================================================================

def get_setting(key, default=""):
    """Get a setting value by key."""
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key, value):
    """Set a setting value (insert or update)."""
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = ?",
            (key, value, datetime.now().isoformat(), value, datetime.now().isoformat())
        )
        conn.commit()
        return {"success": True, "message": f"Setting '{key}' saved!"}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def get_promo_link():
    """Get the saved promo link."""
    return get_setting("promo_link", "")


def set_promo_link(link):
    """Save the promo link."""
    return set_setting("promo_link", link.strip())


def get_daily_usage(plan_id):
    """Get today's usage count for a plan."""
    conn = get_db()
    today = datetime.now().strftime("%Y-%m-%d")
    row = conn.execute(
        "SELECT usage_count FROM daily_usage WHERE plan_id = ? AND date = ?",
        (plan_id, today)
    ).fetchone()
    conn.close()
    return row["usage_count"] if row else 0


def increment_daily_usage(plan_id):
    """Increment today's usage count for a plan."""
    conn = get_db()
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        conn.execute(
            "INSERT INTO daily_usage (plan_id, date, usage_count) VALUES (?, ?, 1) "
            "ON CONFLICT(plan_id, date) DO UPDATE SET usage_count = usage_count + 1",
            (plan_id, today)
        )
        conn.commit()
    finally:
        conn.close()


# ============================================================================
# ACTIVATION CODES
# ============================================================================

def create_code(code, plan_tier):
    """Create a new activation code."""
    if plan_tier not in (1, 2, 3):
        return {"success": False, "error": "Invalid plan tier. Must be 1, 2, or 3."}

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO activation_codes (code, plan_tier) VALUES (?, ?)",
            (code.strip().upper(), plan_tier)
        )
        conn.commit()
        return {"success": True, "message": f"Code '{code}' created for Plan {plan_tier} ({PLANS[plan_tier]['name']})"}
    except sqlite3.IntegrityError:
        return {"success": False, "error": f"Code '{code}' already exists!"}
    finally:
        conn.close()


def get_all_codes():
    """Get all activation codes."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM activation_codes ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_code(code_id):
    """Delete an activation code."""
    conn = get_db()
    conn.execute("DELETE FROM activation_codes WHERE id = ?", (code_id,))
    conn.commit()
    conn.close()
    return {"success": True}


# ============================================================================
# PLAN ACTIVATION
# ============================================================================

def activate_plan(code, user_label=""):
    """Activate a plan using an activation code."""
    conn = get_db()

    # Find the code (case-insensitive, strip whitespace)
    clean_code = code.strip().upper()
    row = conn.execute(
        "SELECT * FROM activation_codes WHERE UPPER(TRIM(code)) = ?", (clean_code,)
    ).fetchone()

    if not row:
        conn.close()
        return {"success": False, "error": "❌ Invalid activation code!"}

    if row["is_used"]:
        conn.close()
        return {"success": False, "error": "⚠️ This code has already been used!"}

    plan_tier = row["plan_tier"]
    plan_name = PLANS[plan_tier]["name"]
    now = datetime.now()
    expires_at = now + timedelta(days=30)

    # Mark code as used
    conn.execute(
        "UPDATE activation_codes SET is_used = 1, used_at = ? WHERE id = ?",
        (now.isoformat(), row["id"])
    )

    # Create active plan
    conn.execute(
        """INSERT INTO active_plans 
           (plan_tier, plan_name, activation_code, user_label, activated_at, expires_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (plan_tier, plan_name, code.strip(), user_label, now.isoformat(), expires_at.isoformat())
    )

    # Log history
    conn.execute(
        "INSERT INTO activation_history (plan_tier, plan_name, activation_code, action) VALUES (?, ?, ?, ?)",
        (plan_tier, plan_name, code.strip(), "ACTIVATED")
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": f"✅ Plan {plan_tier} ({plan_name}) activated successfully!",
        "plan": {
            "tier": plan_tier,
            "name": plan_name,
            "activated_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "days_remaining": 30,
        }
    }


# ============================================================================
# PLAN MANAGEMENT
# ============================================================================

def get_active_plans():
    """Get all active (non-expired) plans."""
    conn = get_db()
    now = datetime.now()

    # Auto-deactivate expired plans
    conn.execute(
        "UPDATE active_plans SET is_active = 0 WHERE expires_at < ? AND is_active = 1",
        (now.isoformat(),)
    )
    conn.commit()

    rows = conn.execute(
        "SELECT * FROM active_plans WHERE is_active = 1 ORDER BY expires_at ASC"
    ).fetchall()
    conn.close()

    plans = []
    for r in rows:
        d = dict(r)
        expires = datetime.fromisoformat(d["expires_at"])
        remaining = (expires - now).days
        d["days_remaining"] = max(0, remaining)
        d["hours_remaining"] = max(0, int((expires - now).total_seconds() // 3600))
        d["is_expired"] = remaining <= 0
        d["plan_info"] = PLANS.get(d["plan_tier"], {})
        plans.append(d)

    return plans


def get_all_plans():
    """Get ALL plans (active + expired)."""
    conn = get_db()
    now = datetime.now()

    # Auto-deactivate expired plans
    conn.execute(
        "UPDATE active_plans SET is_active = 0 WHERE expires_at < ? AND is_active = 1",
        (now.isoformat(),)
    )
    conn.commit()

    rows = conn.execute(
        "SELECT * FROM active_plans ORDER BY created_at DESC"
    ).fetchall()
    conn.close()

    plans = []
    for r in rows:
        d = dict(r)
        expires = datetime.fromisoformat(d["expires_at"])
        remaining = (expires - now).days
        d["days_remaining"] = max(0, remaining)
        d["hours_remaining"] = max(0, int((expires - now).total_seconds() // 3600))
        d["is_expired"] = remaining <= 0 or not d["is_active"]
        d["plan_info"] = PLANS.get(d["plan_tier"], {})
        plans.append(d)

    return plans


def get_expired_plans():
    """Get all expired/deactivated plans."""
    conn = get_db()
    now = datetime.now()

    conn.execute(
        "UPDATE active_plans SET is_active = 0 WHERE expires_at < ? AND is_active = 1",
        (now.isoformat(),)
    )
    conn.commit()

    rows = conn.execute(
        "SELECT * FROM active_plans WHERE is_active = 0 ORDER BY expires_at DESC"
    ).fetchall()
    conn.close()

    return [dict(r) for r in rows]


def delete_plan(plan_id):
    """Delete a plan."""
    conn = get_db()
    plan = conn.execute("SELECT * FROM active_plans WHERE id = ?", (plan_id,)).fetchone()
    if plan:
        conn.execute(
            "INSERT INTO activation_history (plan_tier, plan_name, activation_code, action) VALUES (?, ?, ?, ?)",
            (plan["plan_tier"], plan["plan_name"], plan["activation_code"], "DELETED")
        )
    conn.execute("DELETE FROM active_plans WHERE id = ?", (plan_id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Plan deleted successfully."}


def deactivate_plan(plan_id):
    """Manually deactivate a plan."""
    conn = get_db()
    plan = conn.execute("SELECT * FROM active_plans WHERE id = ?", (plan_id,)).fetchone()
    if plan:
        conn.execute(
            "INSERT INTO activation_history (plan_tier, plan_name, activation_code, action) VALUES (?, ?, ?, ?)",
            (plan["plan_tier"], plan["plan_name"], plan["activation_code"], "DEACTIVATED")
        )
    conn.execute("UPDATE active_plans SET is_active = 0 WHERE id = ?", (plan_id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Plan deactivated."}


def cleanup_expired():
    """Delete all expired plans."""
    conn = get_db()
    now = datetime.now()

    # First deactivate
    conn.execute(
        "UPDATE active_plans SET is_active = 0 WHERE expires_at < ? AND is_active = 1",
        (now.isoformat(),)
    )

    # Then delete all inactive
    result = conn.execute("DELETE FROM active_plans WHERE is_active = 0")
    count = result.rowcount
    conn.commit()
    conn.close()
    return {"success": True, "deleted": count, "message": f"Cleaned up {count} expired plan(s)."}


# ============================================================================
# DASHBOARD STATS
# ============================================================================

def get_dashboard_stats():
    """Get real-time dashboard statistics."""
    conn = get_db()
    now = datetime.now()

    # Auto-cleanup
    conn.execute(
        "UPDATE active_plans SET is_active = 0 WHERE expires_at < ? AND is_active = 1",
        (now.isoformat(),)
    )
    conn.commit()

    # Active plans count
    active_count = conn.execute(
        "SELECT COUNT(*) as c FROM active_plans WHERE is_active = 1"
    ).fetchone()["c"]

    # Expired count
    expired_count = conn.execute(
        "SELECT COUNT(*) as c FROM active_plans WHERE is_active = 0"
    ).fetchone()["c"]

    # Total codes
    total_codes = conn.execute(
        "SELECT COUNT(*) as c FROM activation_codes"
    ).fetchone()["c"]

    # Used codes
    used_codes = conn.execute(
        "SELECT COUNT(*) as c FROM activation_codes WHERE is_used = 1"
    ).fetchone()["c"]

    # Plans by tier
    tier_counts = {}
    for tier in (1, 2, 3):
        count = conn.execute(
            "SELECT COUNT(*) as c FROM active_plans WHERE plan_tier = ? AND is_active = 1",
            (tier,)
        ).fetchone()["c"]
        tier_counts[f"plan_{tier}"] = count

    # Recent activity
    recent = conn.execute(
        "SELECT * FROM activation_history ORDER BY timestamp DESC LIMIT 10"
    ).fetchall()

    conn.close()

    return {
        "active_plans": active_count,
        "expired_plans": expired_count,
        "total_codes": total_codes,
        "used_codes": used_codes,
        "available_codes": total_codes - used_codes,
        "tier_counts": tier_counts,
        "recent_activity": [dict(r) for r in recent],
        "last_updated": now.isoformat(),
    }


# Initialize on import
init_db()
