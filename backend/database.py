"""
FoodVerse AI — Database Layer (SQLite)
Provides persistent storage for real user activity logs, meal plans,
and aggregate dashboard analytics without mock/fake data.
"""

import sqlite3
import os
import json
from datetime import datetime

def get_db_path() -> str:
    return os.environ.get("FOODVERSE_DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), 'foodverse.db'))

DB_PATH = get_db_path()

def get_db():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Activity logs table (food recognition, freshness, hygiene audits, cooked recipes)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        module TEXT NOT NULL,
        title TEXT NOT NULL,
        data_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # AI meal plans table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS meal_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        diet TEXT,
        goal TEXT,
        budget TEXT,
        plan_json TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # User profiles table (Milestone 5, Activity 5.1)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_profiles (
        user_id TEXT PRIMARY KEY,
        profile_json TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

def save_user_profile(user_id: str, profile_data: dict) -> bool:
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_profiles (user_id, profile_json, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                profile_json = excluded.profile_json,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, json.dumps(profile_data)))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[DB PROFILE SAVE ERROR] {e}")
        return False

def get_user_profile(user_id: str) -> dict | None:
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT profile_json FROM user_profiles WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row and row["profile_json"]:
            return json.loads(row["profile_json"])
        return None
    except Exception as e:
        print(f"[DB PROFILE GET ERROR] {e}")
        return None

def log_activity(module: str, title: str, data: dict = None):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO activity_logs (module, title, data_json) VALUES (?, ?, ?)",
            (module, title, json.dumps(data or {}))
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB LOG ERROR] {e}")

def save_meal_plan_db(diet: str, goal: str, budget: str, plan_data: dict):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO meal_plans (diet, goal, budget, plan_json) VALUES (?, ?, ?, ?)",
            (diet, goal, budget, json.dumps(plan_data))
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB SAVE PLAN ERROR] {e}")

def get_latest_meal_plan() -> dict | None:
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, diet, goal, budget, plan_json, created_at FROM meal_plans ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row and row["plan_json"]:
            data = json.loads(row["plan_json"])
            data["id"] = row["id"]
            data["created_at"] = row["created_at"]
            return data
        return None
    except Exception as e:
        print(f"[DB GET PLAN ERROR] {e}")
        return None

def get_recent_activities(limit: int = 20):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, module, title, data_json, created_at FROM activity_logs ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "id": r["id"],
                "module": r["module"],
                "title": r["title"],
                "data": json.loads(r["data_json"]) if r["data_json"] else {},
                "created_at": r["created_at"]
            }
            for r in rows
        ]
    except Exception as e:
        print(f"[DB GET ERROR] {e}")
        return []

def get_dashboard_summary():
    """
    Computes real summary metrics and daily calorie intake from SQLite.
    No hardcoded counts or fake averages.
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Count total meal/food recognition scans
        cursor.execute("SELECT COUNT(*) as total_meals FROM activity_logs WHERE module IN ('food', 'cooking')")
        total_meals = cursor.fetchone()["total_meals"] or 0

        # Count total overall AI scans / audits across all modules
        cursor.execute("SELECT COUNT(*) as total_scans FROM activity_logs")
        total_scans = cursor.fetchone()["total_scans"] or 0
        
        # Compute today's calories and macros from logged meals
        cursor.execute("""
            SELECT data_json FROM activity_logs 
            WHERE module IN ('food', 'cooking') 
              AND DATE(created_at) = DATE('now')
        """)
        today_rows = cursor.fetchall()
        today_calories = 0
        today_protein = 0
        today_carbs = 0
        today_fat = 0
        for r in today_rows:
            try:
                d = json.loads(r["data_json"])
                nut = d.get("nutrition", {})
                cal = nut.get("calories") or d.get("calories", 0)
                today_calories += int(cal)
                today_protein += int(nut.get("protein", 0))
                today_carbs += int(nut.get("carbs", 0))
                today_fat += int(nut.get("fat", 0))
            except Exception:
                pass

        # Module / category distribution
        cursor.execute("""
            SELECT module, COUNT(*) as cnt 
            FROM activity_logs 
            GROUP BY module
        """)
        cat_rows = cursor.fetchall()
        module_labels = {
            'food': 'Food Recognition',
            'freshness': 'Freshness Checks',
            'fresh': 'Freshness Checks',
            'hygiene': 'Hygiene Audits',
            'cooking': 'AI Recipes',
            'cook': 'AI Recipes',
            'plan': 'Meal Plans'
        }
        category_distribution = []
        for cr in cat_rows:
            m = cr["module"]
            category_distribution.append({
                "module": m,
                "name": module_labels.get(m, m.title()),
                "count": cr["cnt"]
            })

        # Compute 7-day calorie totals from real records
        cursor.execute("""
            SELECT strftime('%w', created_at) as day_idx,
                   strftime('%Y-%m-%d', created_at) as log_date,
                   data_json
            FROM activity_logs
            WHERE module IN ('food', 'cooking')
              AND created_at >= DATE('now', '-6 days')
        """)
        week_rows = cursor.fetchall()
        
        day_map = {'0': 'Sun', '1': 'Mon', '2': 'Tue', '3': 'Wed', '4': 'Thu', '5': 'Fri', '6': 'Sat'}
        weekly_cals = {d: 0 for d in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']}
        
        total_macro_protein = 0
        total_macro_carbs = 0
        total_macro_fat = 0

        for r in week_rows:
            d_name = day_map.get(r["day_idx"], 'Mon')
            try:
                data = json.loads(r["data_json"])
                nut = data.get("nutrition", {})
                c = nut.get("calories") or data.get("calories", 0)
                weekly_cals[d_name] += int(c)
                
                total_macro_protein += int(nut.get("protein", 0))
                total_macro_carbs += int(nut.get("carbs", 0))
                total_macro_fat += int(nut.get("fat", 0))
            except Exception:
                pass
        
        conn.close()

        # Format weekly chart data
        weekly_chart = [{"day": day, "calories": weekly_cals[day]} for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']]
        
        # Real Macro split percentages (if any logged, else balanced default)
        macro_sum = total_macro_protein + total_macro_carbs + total_macro_fat
        if macro_sum > 0:
            p_pct = round((total_macro_protein / macro_sum) * 100)
            c_pct = round((total_macro_carbs / macro_sum) * 100)
            f_pct = max(0, 100 - (p_pct + c_pct))
            macro_split = [
                {"name": "Carbs", "value": c_pct, "color": "#fbb03b", "grams": total_macro_carbs},
                {"name": "Protein", "value": p_pct, "color": "#4aa83a", "grams": total_macro_protein},
                {"name": "Fat", "value": f_pct, "color": "#14532d", "grams": total_macro_fat}
            ]
        else:
            macro_split = [
                {"name": "Carbs", "value": 50, "color": "#fbb03b", "grams": 0},
                {"name": "Protein", "value": 25, "color": "#4aa83a", "grams": 0},
                {"name": "Fat", "value": 25, "color": "#14532d", "grams": 0}
            ]

        return {
            "total_meals": total_meals,
            "total_scans": total_scans,
            "today_calories": today_calories,
            "today_macros": {
                "protein": today_protein,
                "carbs": today_carbs,
                "fat": today_fat
            },
            "has_today_meals": len(today_rows) > 0,
            "weekly_calories": weekly_chart,
            "macro_split": macro_split,
            "category_distribution": category_distribution
        }
    except Exception as e:
        print(f"[DB STATS ERROR] {e}")
        return {
            "total_meals": 0,
            "total_scans": 0,
            "today_calories": 0,
            "today_macros": {"protein": 0, "carbs": 0, "fat": 0},
            "has_today_meals": False,
            "weekly_calories": [{"day": d, "calories": 0} for d in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']],
            "macro_split": [
                {"name": "Carbs", "value": 50, "color": "#fbb03b", "grams": 0},
                {"name": "Protein", "value": 25, "color": "#4aa83a", "grams": 0},
                {"name": "Fat", "value": 25, "color": "#14532d", "grams": 0}
            ],
            "category_distribution": []
        }

init_db()
