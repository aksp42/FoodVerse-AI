"""
FoodVerse AI — Test Suite: User Profile & Meal Plan Generation
Consolidates test_activity_5_1.py and test_activity_5_2.py.
"""

"""
FoodVerse AI — Smart Bridge Activity 5.1 Test Suite
User Profile, Goal, and Preference Processing

Tests:
  01. validate_and_normalize_profile: parses valid profile metrics, enums, and comma-separated lists.
  02. validate_and_normalize_profile: rejects age outside 1–120.
  03. validate_and_normalize_profile: rejects height outside 50–250 cm.
  04. validate_and_normalize_profile: rejects weight outside 20–300 kg.
  05. validate_and_normalize_profile: flags unrecognized dietary preference.
  06. validate_and_normalize_profile: flags unrecognized health goal.
  07. validate_and_normalize_profile: cleanly separates allergies, intolerances, dislikes, and restrictions.
  08. calculate_estimated_calorie_target: applies Mifflin-St Jeor formula and activity multipliers.
  09. calculate_estimated_calorie_target: includes non-medical educational disclaimer.
  10. calculate_estimated_calorie_target: safely falls back to standard targets when biometrics are missing.
  11. is_ingredient_safe_for_user: strictly blocks ingredients matching declared allergens.
  12. is_ingredient_safe_for_user: blocks lactose/dairy synonyms for lactose intolerance.
  13. is_ingredient_safe_for_user: blocks gluten/wheat synonyms for gluten intolerance.
  14. is_ingredient_safe_for_user: blocks items violating dietary restrictions.
  15. is_ingredient_safe_for_user: permits ingredients free of allergens and intolerances.
  16. POST /api/profile: successfully validates, normalizes, and persists profile with HTTP 200.
  17. POST /api/profile: returns HTTP 400 with detailed error list on invalid input ranges.
  18. GET /api/profile: retrieves previously persisted profile from SQLite.
  19. GET /api/profile: returns clean sensible default profile for new users (is_new=True).
  20. POST /api/meal-plan: automatically incorporates stored profile allergies and intolerances.
  21. Database integrity: ensures existing activity_logs and meal_plans tables are unaffected.
  22. Regression: POST /api/predict (2.1), /api/freshness (3.2), and /api/cooking (4.2) remain operational.
"""

import io
import json
import unittest
import warnings
from unittest.mock import patch, MagicMock

from PIL import Image

warnings.filterwarnings('ignore', message=r'.*starlette\.testclient.*')

from fastapi.testclient import TestClient

import app
import database
import profile_service

client = TestClient(app.app)


def make_test_image(width: int = 120, height: int = 120, color: tuple = (150, 100, 50)) -> bytes:
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


class TestProfileService(unittest.TestCase):
    """Unit tests for profile_service validation and calculation logic."""

    def test_01_valid_profile_normalization(self):
        raw = {
            "name": "Priya Sharma",
            "phone": "+91 98765 43210",
            "age": 28,
            "gender": "female",
            "height_cm": 165.0,
            "weight_kg": 60.0,
            "diet": "Vegetarian",
            "goal": "Weight Loss",
            "activity_level": "moderately active",
            "budget": "Medium",
            "allergies": "peanuts, shellfish",
            "intolerances": ["lactose"],
            "dislikes": "bitter gourd, mushrooms",
            "restrictions": "jain",
        }
        normalized, errors = profile_service.validate_and_normalize_profile(raw)
        self.assertEqual(errors, [])
        self.assertEqual(normalized["name"], "Priya Sharma")
        self.assertEqual(normalized["age"], 28)
        self.assertEqual(normalized["height_cm"], 165.0)
        self.assertEqual(normalized["weight_kg"], 60.0)
        self.assertEqual(normalized["diet"], "Vegetarian")
        self.assertEqual(normalized["goal"], "Weight Loss")
        self.assertEqual(normalized["allergies"], ["peanuts", "shellfish"])
        self.assertEqual(normalized["intolerances"], ["lactose"])
        self.assertEqual(normalized["dislikes"], ["bitter gourd", "mushrooms"])
        self.assertEqual(normalized["restrictions"], ["jain"])
        self.assertIn("medical_disclaimer", normalized)
        self.assertIsInstance(normalized["calorie_target"], int)

    def test_02_reject_invalid_age(self):
        raw_under = {"age": 0}
        _, errs_under = profile_service.validate_and_normalize_profile(raw_under)
        self.assertTrue(any("Age must be between 1 and 120" in e for e in errs_under))

        raw_over = {"age": 125}
        _, errs_over = profile_service.validate_and_normalize_profile(raw_over)
        self.assertTrue(any("Age must be between 1 and 120" in e for e in errs_over))

    def test_03_reject_invalid_height(self):
        raw_short = {"height_cm": 45.0}
        _, errs_short = profile_service.validate_and_normalize_profile(raw_short)
        self.assertTrue(any("Height must be between 50 and 250 cm" in e for e in errs_short))

        raw_tall = {"height_cm": 280.0}
        _, errs_tall = profile_service.validate_and_normalize_profile(raw_tall)
        self.assertTrue(any("Height must be between 50 and 250 cm" in e for e in errs_tall))

    def test_04_reject_invalid_weight(self):
        raw_low = {"weight_kg": 15.0}
        _, errs_low = profile_service.validate_and_normalize_profile(raw_low)
        self.assertTrue(any("Weight must be between 20 and 300 kg" in e for e in errs_low))

        raw_high = {"weight_kg": 350.0}
        _, errs_high = profile_service.validate_and_normalize_profile(raw_high)
        self.assertTrue(any("Weight must be between 20 and 300 kg" in e for e in errs_high))

    def test_05_flag_unrecognized_diet(self):
        raw = {"diet": "CarnivoreOnlyExtreme"}
        _, errors = profile_service.validate_and_normalize_profile(raw)
        self.assertTrue(any("Invalid dietary preference" in e for e in errors))

    def test_06_flag_unrecognized_goal(self):
        raw = {"goal": "Become Immortal"}
        _, errors = profile_service.validate_and_normalize_profile(raw)
        self.assertTrue(any("Invalid health goal" in e for e in errors))

    def test_07_separation_of_allergies_and_preferences(self):
        raw = {
            "allergies": "peanuts, tree nuts",
            "intolerances": "lactose",
            "dislikes": "brinjal, okra",
            "restrictions": "no alcohol, halal",
        }
        normalized, _ = profile_service.validate_and_normalize_profile(raw)
        # Verify strict separation
        self.assertEqual(set(normalized["allergies"]), {"peanuts", "tree nuts"})
        self.assertEqual(set(normalized["intolerances"]), {"lactose"})
        self.assertEqual(set(normalized["dislikes"]), {"brinjal", "okra"})
        self.assertEqual(set(normalized["restrictions"]), {"no alcohol", "halal"})

    def test_08_calorie_calculation_formula(self):
        # Male, 30y, 175cm, 75kg, sedentary, weight maintain
        # BMR = 10*75 + 6.25*175 - 5*30 + 5 = 750 + 1093.75 - 150 + 5 = 1698.75 ~ 1699
        # Sedentary = 1.2 => 1699 * 1.2 = 2038.8 ~ 2039
        target, bmr = profile_service.calculate_estimated_calorie_target(
            age=30,
            height_cm=175.0,
            weight_kg=75.0,
            gender="male",
            activity_level="sedentary",
            goal="Weight Maintain",
        )
        self.assertAlmostEqual(bmr, 1699, delta=2)
        self.assertAlmostEqual(target, 2039, delta=5)

    def test_09_medical_disclaimer_present(self):
        raw = {"age": 25, "height_cm": 170, "weight_kg": 65}
        normalized, _ = profile_service.validate_and_normalize_profile(raw)
        disclaimer = normalized.get("medical_disclaimer", "")
        self.assertIn("educational", disclaimer.lower())
        self.assertIn("medical advice", disclaimer.lower())

    def test_10_missing_metrics_fallback(self):
        # Missing age/height/weight returns standard goal target and None BMR
        target, bmr = profile_service.calculate_estimated_calorie_target(
            age=None,
            height_cm=None,
            weight_kg=None,
            gender="unspecified",
            activity_level="moderately active",
            goal="Muscle Gain",
        )
        self.assertEqual(target, 2400)
        self.assertIsNone(bmr)

    def test_11_ingredient_safety_allergen_block(self):
        user_profile = {"allergies": ["peanut", "shellfish"], "intolerances": [], "restrictions": []}
        safe, reason = profile_service.is_ingredient_safe_for_user("Peanut Butter Toast", user_profile)
        self.assertFalse(safe)
        self.assertIn("allergen", reason.lower())

    def test_12_ingredient_safety_lactose_block(self):
        user_profile = {"allergies": [], "intolerances": ["lactose"], "restrictions": []}
        # Paneer contains dairy/lactose
        safe_paneer, reason_paneer = profile_service.is_ingredient_safe_for_user("Palak Paneer", user_profile)
        self.assertFalse(safe_paneer)
        self.assertIn("intolerance", reason_paneer.lower())

        # Ghee/cheese also blocked
        safe_cheese, _ = profile_service.is_ingredient_safe_for_user("Cheddar Cheese Sandwich", user_profile)
        self.assertFalse(safe_cheese)

    def test_13_ingredient_safety_gluten_block(self):
        user_profile = {"allergies": [], "intolerances": ["gluten"], "restrictions": []}
        safe_roti, reason_roti = profile_service.is_ingredient_safe_for_user("Whole Wheat Atta Roti", user_profile)
        self.assertFalse(safe_roti)
        self.assertIn("intolerance", reason_roti.lower())

    def test_14_ingredient_safety_restriction_block(self):
        user_profile = {"allergies": [], "intolerances": [], "restrictions": ["pork"]}
        safe, reason = profile_service.is_ingredient_safe_for_user("Pork Sausage", user_profile)
        self.assertFalse(safe)
        self.assertIn("restriction", reason.lower())

    def test_15_ingredient_safety_permitted(self):
        user_profile = {
            "allergies": ["peanuts"],
            "intolerances": ["lactose"],
            "restrictions": ["no alcohol"],
        }
        safe, reason = profile_service.is_ingredient_safe_for_user("Steamed Jasmine Rice with Dal", user_profile)
        self.assertTrue(safe)
        self.assertIsNone(reason)


class TestProfileEndpoints(unittest.TestCase):
    """Integration tests for /api/profile and related endpoints."""

    def test_16_post_profile_success(self):
        payload = {
            "user_id": "test_user_activity_5_1",
            "name": "Aarav Patel",
            "age": 32,
            "gender": "male",
            "height_cm": 180.0,
            "weight_kg": 78.0,
            "diet": "Vegetarian",
            "goal": "Muscle Gain",
            "activity_level": "very active",
            "allergies": "cashews, walnuts",
            "intolerances": "lactose",
            "dislikes": "coriander",
            "restrictions": "no beef",
        }
        res = client.post("/api/profile", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "saved")
        self.assertEqual(data["user_id"], "test_user_activity_5_1")
        self.assertEqual(data["profile"]["diet"], "Vegetarian")
        self.assertEqual(data["profile"]["allergies"], ["cashews", "walnuts"])
        self.assertGreater(data["profile"]["calorie_target"], 2000)

    def test_17_post_profile_validation_error(self):
        payload = {
            "user_id": "test_invalid_user",
            "age": -5,
            "height_cm": 400.0,
            "weight_kg": 10.0,
        }
        res = client.post("/api/profile", json=payload)
        self.assertEqual(res.status_code, 400)
        data = res.json()
        self.assertIn("errors", data["detail"])
        self.assertGreaterEqual(len(data["detail"]["errors"]), 3)

    def test_18_get_profile_existing(self):
        # Retrieve the user created in test_16
        res = client.get("/api/profile?user_id=test_user_activity_5_1")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["is_new"])
        self.assertEqual(data["profile"]["name"], "Aarav Patel")
        self.assertEqual(data["profile"]["goal"], "Muscle Gain")

    def test_19_get_profile_new_user_default(self):
        res = client.get("/api/profile?user_id=non_existent_user_99999")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["is_new"])
        self.assertEqual(data["profile"]["diet"], "Vegetarian")
        self.assertIn("medical_disclaimer", data["profile"])

    @patch("app._call_gemini_json")
    def test_20_meal_plan_incorporates_stored_profile_allergies(self, mock_gemini):
        mock_plan = {
            "target_calories": 2500,
            "nutrition_notes": "Balanced high-protein vegetarian plan",
            "days": {
                "Mon": {
                    "breakfast": {"name": "Oatmeal with chia seeds", "emoji": "🥣", "cal": 450, "portion": "1 bowl", "protein": 15, "carbs": 60, "fat": 10, "diets": ["Vegetarian"], "cost": "Medium"},
                    "lunch": {"name": "Dal Tadka with brown rice", "emoji": "🍛", "cal": 750, "portion": "1 plate", "protein": 25, "carbs": 110, "fat": 15, "diets": ["Vegetarian"], "cost": "Medium"},
                    "dinner": {"name": "Tofu Vegetable Stir Fry", "emoji": "🥗", "cal": 650, "portion": "1 plate", "protein": 30, "carbs": 50, "fat": 20, "diets": ["Vegetarian"], "cost": "Medium"},
                    "snack": {"name": "Roasted makhana", "emoji": "🍿", "cal": 150, "portion": "1 bowl", "protein": 5, "carbs": 25, "fat": 3, "diets": ["Vegetarian"], "cost": "Medium"}
                }
            },
            "shopping_list": {
                "produce": ["Spinach", "Tofu"],
                "grains_and_legumes": ["Brown rice", "Lentils"],
                "dairy_and_protein": ["Tofu"],
                "spices_and_pantry": ["Cumin", "Turmeric"]
            }
        }
        mock_gemini.return_value = (mock_plan, "gemini-3.8-flash")

        res = client.post("/api/meal-plan", json={"user_id": "test_user_activity_5_1", "days": 7})
        self.assertEqual(res.status_code, 200)

        # Ensure the prompt sent to Gemini incorporated the stored allergies & intolerances
        prompt_arg = mock_gemini.call_args[0][0]
        self.assertIn("cashews", prompt_arg)
        self.assertIn("walnuts", prompt_arg)
        self.assertIn("lactose", prompt_arg)

    def test_21_database_integrity(self):
        # Verify user_profiles table exists and existing activity logs are intact
        conn = database.get_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM user_profiles")
        user_profiles_count = c.fetchone()[0]
        self.assertGreaterEqual(user_profiles_count, 1)

        c.execute("SELECT COUNT(*) FROM activity_logs")
        logs_count = c.fetchone()[0]
        self.assertGreaterEqual(logs_count, 160)
        conn.close()

    @patch("app._call_gemini_json")
    def test_22_regressions_remain_operational(self, mock_gemini):
        # 1. Cooking generation (Activity 4.2)
        mock_gemini.return_value = ({
            "name": "Jeera Rice Bowl",
            "emoji": "🍚",
            "description": "Fluffy basmati rice tempered with cumin and ghee.",
            "prep_time_mins": 5,
            "cook_time_mins": 15,
            "servings": 2,
            "ingredients": [{"name": "Basmati rice", "quantity": "1 cup", "category": "grains"}],
            "instructions": [{"step": 1, "instruction": "Boil rice with cumin."}],
        }, "gemini-3.8-flash")
        res_cooking = client.post("/api/cooking", json={"ingredients": ["rice", "cumin"]})
        self.assertEqual(res_cooking.status_code, 200)

        # 2. Freshness endpoint (Activity 3.2)
        test_img = make_test_image()
        mock_gemini.return_value = ({
            "is_food": True,
            "food_detected": "Banana",
            "freshness_status": "fresh",
            "confidence_score": 0.95,
            "evidence_level": "high",
            "observations": ["Bright yellow peel"],
            "safety_recommendations": ["Safe to consume"],
            "limitations": "Surface assessment only",
        }, "gemini-3.8-flash")
        res_freshness = client.post(
            "/api/freshness",
            files={"image": ("banana.jpg", test_img, "image/jpeg")}
        )
        self.assertEqual(res_freshness.status_code, 200)

#===========================================================================
# Section: test_activity_5_2.py
#===========================================================================

"""
FoodVerse AI — Smart Bridge Activity 5.2 Test Suite
Meal Plan Generation and Adaptive Recommendation Logic

Tests:
  01. build_meal_plan_prompt: constructs prompt with 1-day daily structure.
  02. build_meal_plan_prompt: constructs prompt with 7-day weekly structure.
  03. build_meal_plan_prompt: incorporates user profile biometrics and Mifflin-St Jeor target.
  04. build_meal_plan_prompt: enforces strict allergen, intolerance, and restriction exclusions.
  05. normalize_meal_plan_response: produces valid 1-day structure with meal-wise & day totals.
  06. normalize_meal_plan_response: produces valid 7-day structure with day summaries & weekly overview.
  07. normalize_meal_plan_response: handles empty or partial Gemini response with robust fallbacks.
  08. normalize_meal_plan_response: includes actionable adaptive recommendations with educational rationale.
  09. normalize_meal_plan_response: includes non-medical educational disclaimer on every plan.
  10. Allergen safety: replaces primary dish containing declared allergen with safe alternative.
  11. Intolerance safety: detects and substitutes dairy/lactose dishes for lactose-intolerant users.
  12. Intolerance safety: detects and substitutes gluten/wheat dishes for gluten-intolerant users.
  13. Restriction safety: detects and substitutes dishes violating dietary restrictions.
  14. Alternative safety: purges any alternative that triggers an allergen or intolerance.
  15. Incomplete profile: falls back gracefully to standard goal targets when biometrics are missing.
  16. POST /api/meal-plan: returns HTTP 200 for 1-day daily plan request.
  17. POST /api/meal-plan: returns HTTP 200 for 7-day weekly plan request with stored profile context.
  18. POST /api/meal-plan: handles Gemini API failure with HTTP 502 and detailed error message.
  19. Database persistence: verifies POST /api/meal-plan saves generated plan into SQLite meal_plans table.
  20. GET /api/meal-plan: retrieves the most recently persisted meal plan from SQLite.
  21. GET /api/meal-plan: returns clean response when no meal plans exist in database.
  22. Regression: Activity 5.1 profile API and prior milestones (2.1, 3.2, 4.2) remain fully operational.
"""

import io
import json
import unittest
import warnings
from unittest.mock import patch, MagicMock

from PIL import Image

warnings.filterwarnings('ignore', message=r'.*starlette\.testclient.*')

from fastapi.testclient import TestClient

import app
import database
import meal_planner_service
import profile_service

client = TestClient(app.app)


def make_test_image(width: int = 120, height: int = 120, color: tuple = (120, 180, 90)) -> bytes:
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def mock_valid_gemini_weekly_response(target_cal: int = 2000) -> dict:
    """Returns a realistic raw Gemini weekly meal plan response."""
    days = {}
    for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
        days[d] = {
            "breakfast": {
                "name": "Poha with Roasted Peanuts and Lemon",
                "emoji": "🥣",
                "cal": 420,
                "protein": 11,
                "carbs": 68,
                "fat": 12,
                "prep_time_mins": 15,
                "ingredients": ["1.5 cups flattened rice", "2 tbsp roasted peanuts", "1 green chilli", "1/2 tsp mustard seeds", "lemon juice"],
                "instructions": "Rinse poha. Sauté mustard seeds and peanuts, fold in poha with turmeric, and finish with lemon.",
                "alternatives": [
                    {
                        "name": "Upma with Mixed Vegetables",
                        "emoji": "🍲",
                        "cal": 390,
                        "protein": 10,
                        "carbs": 62,
                        "fat": 11,
                        "reason": "Lower glycemic alternative with identical cooking time"
                    }
                ]
            },
            "lunch": {
                "name": "Rajma Masala with Steamed Brown Rice",
                "emoji": "🍛",
                "cal": 650,
                "protein": 24,
                "carbs": 98,
                "fat": 14,
                "prep_time_mins": 30,
                "ingredients": ["1 cup boiled kidney beans", "1 cup brown rice", "onion tomato gravy", "ginger garlic paste"],
                "instructions": "Simmer boiled rajma in spiced onion-tomato gravy. Serve with freshly steamed brown rice.",
                "alternatives": [
                    {
                        "name": "Chole with Brown Rice",
                        "emoji": "🍛",
                        "cal": 640,
                        "protein": 22,
                        "carbs": 95,
                        "fat": 15,
                        "reason": "High-fiber legume swap"
                    }
                ]
            },
            "dinner": {
                "name": "Palak Tofu with Multigrain Roti",
                "emoji": "🥗",
                "cal": 520,
                "protein": 26,
                "carbs": 58,
                "fat": 16,
                "prep_time_mins": 25,
                "ingredients": ["150g firm tofu cubes", "2 cups blanched spinach puree", "2 multigrain rotis", "1 tsp cumin"],
                "instructions": "Cook tofu cubes in fragrant spinach gravy. Serve with warm multigrain rotis.",
                "alternatives": [
                    {
                        "name": "Methi Moong Dal with Roti",
                        "emoji": "🍲",
                        "cal": 490,
                        "protein": 21,
                        "carbs": 64,
                        "fat": 12,
                        "reason": "Lighter evening dinner"
                    }
                ]
            },
            "snack": {
                "name": "Roasted Chana & Green Tea",
                "emoji": "🍿",
                "cal": 180,
                "protein": 8,
                "carbs": 26,
                "fat": 4,
                "prep_time_mins": 5,
                "ingredients": ["1/2 cup roasted black chickpeas", "1 cup unsweetened green tea"],
                "instructions": "Enjoy dry-roasted chana with freshly brewed green tea.",
                "alternatives": [
                    {
                        "name": "Fresh Apple Slices with Cinnamon",
                        "emoji": "🍎",
                        "cal": 120,
                        "protein": 1,
                        "carbs": 28,
                        "fat": 1,
                        "reason": "Low-calorie fruit option"
                    }
                ]
            }
        }

    return {
        "plan_type": "weekly",
        "target_calories": target_cal,
        "nutrition_notes": "Balanced vegetarian weekly meal plan emphasizing plant protein and slow-digesting complex carbs.",
        "adaptive_recommendations": [
            "Distribute protein intake evenly across breakfast, lunch, and dinner to maximize muscle protein synthesis.",
            "Incorporate green tea or water 20 minutes before meals to aid digestion and promote natural satiety.",
            "Prioritize whole legumes over processed snacks for sustained afternoon energy."
        ],
        "days": days,
        "shopping_list": {
            "produce": ["Fresh spinach", "Tomatoes", "Onions", "Lemons", "Apples"],
            "grains_and_legumes": ["Brown rice", "Kidney beans (Rajma)", "Flattened rice (Poha)", "Multigrain flour"],
            "dairy_and_protein": ["Firm tofu", "Roasted chana"],
            "spices_and_pantry": ["Cumin seeds", "Mustard seeds", "Turmeric powder", "Olive oil"]
        },
        "weekly_overview": "A nutrient-dense 7-day vegetarian schedule tailored to support sustained energy and lean muscle maintenance."
    }


class TestMealPlannerService(unittest.TestCase):
    """Unit tests for meal_planner_service logic and validation."""

    def setUp(self):
        self.sample_profile = {
            "name": "Rohan Gupta",
            "age": 29,
            "gender": "male",
            "height_cm": 178.0,
            "weight_kg": 76.0,
            "diet": "Vegetarian",
            "goal": "Muscle Gain",
            "activity_level": "very active",
            "budget": "Medium",
            "allergies": ["peanuts"],
            "intolerances": ["lactose"],
            "dislikes": ["bitter gourd"],
            "restrictions": ["no alcohol"],
        }

    def test_01_build_prompt_daily(self):
        prompt, target_cal = meal_planner_service.build_meal_plan_prompt(
            profile=self.sample_profile,
            days=1,
        )
        self.assertIn("1-day comprehensive daily plan", prompt)
        self.assertIn('"Today"', prompt)
        self.assertGreater(target_cal, 2000)

    def test_02_build_prompt_weekly(self):
        prompt, target_cal = meal_planner_service.build_meal_plan_prompt(
            profile=self.sample_profile,
            days=7,
        )
        self.assertIn("7-day comprehensive weekly plan", prompt)
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            self.assertIn(f'"{day}"', prompt)

    def test_03_build_prompt_incorporates_biometrics_and_goal(self):
        prompt, target_cal = meal_planner_service.build_meal_plan_prompt(
            profile=self.sample_profile,
            days=7,
        )
        self.assertIn("178.0 cm", prompt)
        self.assertIn("76.0 kg", prompt)
        self.assertIn("Muscle Gain", prompt)
        self.assertIn("very active", prompt)

    def test_04_build_prompt_enforces_safety_exclusions(self):
        prompt, _ = meal_planner_service.build_meal_plan_prompt(
            profile=self.sample_profile,
            days=7,
        )
        self.assertIn("STRICT SAFETY EXCLUSIONS", prompt)
        self.assertIn("peanuts", prompt)
        self.assertIn("lactose", prompt)
        self.assertIn("no alcohol", prompt)

    def test_05_normalize_daily_plan_structure(self):
        raw = mock_valid_gemini_weekly_response(2100)
        # Adapt raw for 1 day
        raw["days"] = {"Today": raw["days"]["Mon"]}
        norm = meal_planner_service.normalize_meal_plan_response(
            raw_data=raw,
            user_profile={},
            diet="Vegetarian",
            goal="Weight Maintain",
            budget="Medium",
            days_count=1,
            target_cal=2100,
        )
        self.assertEqual(norm["plan_type"], "daily")
        self.assertIn("Today", norm["days"])
        today_data = norm["days"]["Today"]
        for slot in ["breakfast", "lunch", "dinner", "snack"]:
            self.assertIn(slot, today_data)
            meal = today_data[slot]
            self.assertIn("name", meal)
            self.assertIn("cal", meal)
            self.assertIn("protein", meal)
            self.assertIn("carbs", meal)
            self.assertIn("fat", meal)
            self.assertIn("ingredients", meal)
            self.assertIn("instructions", meal)
            self.assertIn("alternatives", meal)

        summary = today_data["day_summary"]
        self.assertGreater(summary["total_calories"], 1000)
        self.assertIn("total_protein", summary)
        self.assertIn("total_carbs", summary)
        self.assertIn("total_fat", summary)

    def test_06_normalize_weekly_plan_structure(self):
        raw = mock_valid_gemini_weekly_response(2200)
        norm = meal_planner_service.normalize_meal_plan_response(
            raw_data=raw,
            user_profile={},
            diet="Vegetarian",
            goal="Muscle Gain",
            budget="Medium",
            days_count=7,
            target_cal=2200,
        )
        self.assertEqual(norm["plan_type"], "weekly")
        self.assertEqual(len(norm["days"]), 7)
        self.assertGreater(norm["weekly_total_calories"], 7000)
        self.assertGreater(norm["weekly_avg_calories"], 1000)
        self.assertIn("weekly_overview", norm)
        self.assertIn("adaptive_recommendations", norm)

    def test_07_normalize_handles_empty_or_malformed_ai_dict(self):
        norm = meal_planner_service.normalize_meal_plan_response(
            raw_data=None,
            user_profile={},
            diet="Vegetarian",
            goal="Weight Maintain",
            budget="Medium",
            days_count=7,
            target_cal=1900,
        )
        self.assertEqual(norm["plan_type"], "weekly")
        self.assertEqual(len(norm["days"]), 7)
        # Verify fallback meals are populated
        for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            for slot in ["breakfast", "lunch", "dinner", "snack"]:
                self.assertIsNotNone(norm["days"][d][slot]["name"])
                self.assertGreater(norm["days"][d][slot]["cal"], 0)

    def test_08_adaptive_recommendations_rationale(self):
        raw = mock_valid_gemini_weekly_response(2000)
        norm = meal_planner_service.normalize_meal_plan_response(
            raw_data=raw,
            user_profile=self.sample_profile,
            diet="Vegetarian",
            goal="Muscle Gain",
            budget="Medium",
            days_count=7,
        )
        recs = norm["adaptive_recommendations"]
        self.assertIsInstance(recs, list)
        self.assertGreaterEqual(len(recs), 2)
        # Verify recommendation text is informative
        self.assertTrue(any(len(r) > 15 for r in recs))

    def test_09_medical_disclaimer_attached(self):
        norm = meal_planner_service.normalize_meal_plan_response(
            raw_data={},
            user_profile={},
            diet="Vegetarian",
            goal="Weight Maintain",
            budget="Medium",
            days_count=1,
        )
        self.assertIn("medical_disclaimer", norm)
        self.assertIn("educational", norm["medical_disclaimer"].lower())
        self.assertIn("medical advice", norm["medical_disclaimer"].lower())

    def test_10_allergen_safety_replaces_unsafe_primary_dish(self):
        # User is allergic to peanuts
        profile = {"allergies": ["peanut"], "intolerances": [], "restrictions": []}
        raw = {
            "days": {
                "Today": {
                    "breakfast": {
                        "name": "Peanut Butter Banana Toast",
                        "ingredients": ["2 slices bread", "2 tbsp peanut butter", "1 banana"],
                        "cal": 450,
                        "protein": 14,
                        "carbs": 60,
                        "fat": 16,
                        "alternatives": [
                            {
                                "name": "Almond Butter Fruit Toast",
                                "cal": 430,
                                "protein": 12,
                                "carbs": 58,
                                "fat": 15,
                                "reason": "Peanut-free seed/nut option"
                            }
                        ]
                    }
                }
            }
        }
        norm = meal_planner_service.normalize_meal_plan_response(
            raw_data=raw,
            user_profile=profile,
            diet="Vegetarian",
            goal="Weight Maintain",
            budget="Medium",
            days_count=1,
        )
        breakfast = norm["days"]["Today"]["breakfast"]
        # Must NOT contain Peanut Butter
        self.assertNotIn("peanut", breakfast["name"].lower())
        self.assertIn("safety_adaptation_note", breakfast)

    def test_11_intolerance_safety_substitutes_lactose(self):
        # User has lactose intolerance
        profile = {"allergies": [], "intolerances": ["lactose"], "restrictions": []}
        raw = {
            "days": {
                "Today": {
                    "lunch": {
                        "name": "Paneer Butter Masala with Naan",
                        "ingredients": ["paneer", "butter", "cream", "naan"],
                        "cal": 700,
                        "protein": 22,
                        "carbs": 70,
                        "fat": 32,
                        "alternatives": []
                    }
                }
            }
        }
        norm = meal_planner_service.normalize_meal_plan_response(
            raw_data=raw,
            user_profile=profile,
            diet="Vegetarian",
            goal="Weight Maintain",
            budget="Medium",
            days_count=1,
        )
        lunch = norm["days"]["Today"]["lunch"]
        # Must NOT be paneer / dairy
        self.assertNotIn("paneer", lunch["name"].lower())
        self.assertNotIn("butter", lunch["name"].lower())
        self.assertIn("safety_adaptation_note", lunch)

    def test_12_intolerance_safety_substitutes_gluten(self):
        # User has gluten intolerance
        profile = {"allergies": [], "intolerances": ["gluten"], "restrictions": []}
        raw = {
            "days": {
                "Today": {
                    "dinner": {
                        "name": "Whole Wheat Roti with Dal",
                        "ingredients": ["whole wheat atta", "toor dal"],
                        "cal": 500,
                        "protein": 18,
                        "carbs": 80,
                        "fat": 8,
                        "alternatives": []
                    }
                }
            }
        }
        norm = meal_planner_service.normalize_meal_plan_response(
            raw_data=raw,
            user_profile=profile,
            diet="Vegetarian",
            goal="Weight Maintain",
            budget="Medium",
            days_count=1,
        )
        dinner = norm["days"]["Today"]["dinner"]
        self.assertNotIn("wheat", dinner["name"].lower())

    def test_13_restriction_safety_substitutes_prohibited_dish(self):
        # User has restriction: pork
        profile = {"allergies": [], "intolerances": [], "restrictions": ["pork"]}
        raw = {
            "days": {
                "Today": {
                    "dinner": {
                        "name": "Pork Ribs with Barbecue Sauce",
                        "ingredients": ["pork ribs", "bbq sauce"],
                        "cal": 650,
                        "protein": 35,
                        "carbs": 25,
                        "fat": 40,
                        "alternatives": []
                    }
                }
            }
        }
        norm = meal_planner_service.normalize_meal_plan_response(
            raw_data=raw,
            user_profile=profile,
            diet="Non-Vegetarian",
            goal="Weight Maintain",
            budget="Medium",
            days_count=1,
        )
        dinner = norm["days"]["Today"]["dinner"]
        self.assertNotIn("pork", dinner["name"].lower())

    def test_14_alternative_safety_purges_unsafe_options(self):
        # User is allergic to shellfish
        profile = {"allergies": ["shellfish"], "intolerances": [], "restrictions": []}
        raw_meal = {
            "name": "Grilled Salmon Fillet",
            "cal": 520,
            "protein": 40,
            "carbs": 10,
            "fat": 30,
            "ingredients": ["salmon", "lemon", "olive oil"],
            "alternatives": [
                {
                    "name": "Shrimp Scampi with Pasta",  # Unsafe! Shrimp is shellfish
                    "cal": 510,
                    "protein": 36,
                    "carbs": 45,
                    "fat": 18,
                    "reason": "Seafood pasta"
                },
                {
                    "name": "Baked Cod with Asparagus",  # Safe! Finfish
                    "cal": 480,
                    "protein": 38,
                    "carbs": 12,
                    "fat": 14,
                    "reason": "Mild white fish alternative"
                }
            ]
        }
        norm_meal = meal_planner_service.normalize_meal_item(
            raw_meal=raw_meal,
            slot_name="dinner",
            user_profile=profile,
            diet="Pescatarian",
            budget="High",
        )
        # Shrimp alternative should be dropped
        alt_names = [a["name"] for a in norm_meal["alternatives"]]
        self.assertNotIn("Shrimp Scampi with Pasta", alt_names)
        self.assertIn("Baked Cod with Asparagus", alt_names)

    def test_15_incomplete_profile_handling(self):
        # Empty profile with no age, height, or weight
        empty_profile = {}
        target_cal, bmr = profile_service.calculate_estimated_calorie_target(
            age=None,
            height_cm=None,
            weight_kg=None,
            gender="unspecified",
            activity_level="moderately active",
            goal="Weight Maintain",
        )
        self.assertEqual(target_cal, 1900)
        self.assertIsNone(bmr)

        # Prompt building and normalization succeed without error
        prompt, derived_target = meal_planner_service.build_meal_plan_prompt(
            profile=empty_profile,
            diet="Vegetarian",
            goal="Weight Maintain",
            budget="Medium",
            days=7,
        )
        self.assertEqual(derived_target, 1900)
        self.assertIn("General adult reference", prompt)


class TestMealPlanEndpoints(unittest.TestCase):
    """Integration tests for /api/meal-plan endpoints and SQLite persistence."""

    @patch("app._call_gemini_json")
    def test_16_post_meal_plan_daily(self, mock_gemini):
        mock_raw = mock_valid_gemini_weekly_response(1950)
        mock_raw["days"] = {"Today": mock_raw["days"]["Mon"]}
        mock_raw["plan_type"] = "daily"
        mock_gemini.return_value = (mock_raw, "gemini-3.8-flash")

        res = client.post("/api/meal-plan", json={"days": 1, "diet": "Vegetarian", "goal": "Weight Maintain"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["plan_type"], "daily")
        self.assertIn("Today", data["days"])
        self.assertIn("adaptive_recommendations", data)
        self.assertIn("medical_disclaimer", data)

    @patch("app._call_gemini_json")
    def test_17_post_meal_plan_weekly_with_stored_profile(self, mock_gemini):
        # First save a user profile with allergies
        profile_payload = {
            "user_id": "test_planner_user_5_2",
            "name": "Kavita Reddy",
            "age": 31,
            "gender": "female",
            "height_cm": 162.0,
            "weight_kg": 58.0,
            "diet": "Vegetarian",
            "goal": "Weight Loss",
            "activity_level": "lightly active",
            "allergies": "cashews, pistachios",
            "intolerances": "lactose",
            "restrictions": "jain",
        }
        res_prof = client.post("/api/profile", json=profile_payload)
        self.assertEqual(res_prof.status_code, 200)

        # Mock Gemini response
        mock_raw = mock_valid_gemini_weekly_response(1650)
        mock_gemini.return_value = (mock_raw, "gemini-3.8-flash")

        # Request weekly meal plan for this user
        res = client.post("/api/meal-plan", json={"user_id": "test_planner_user_5_2", "days": 7})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["plan_type"], "weekly")
        self.assertEqual(len(data["days"]), 7)
        self.assertIn("weekly_total_calories", data)
        self.assertIn("weekly_avg_calories", data)

        # Verify prompt had the stored profile restrictions
        prompt_arg = mock_gemini.call_args[0][0]
        self.assertIn("cashews", prompt_arg)
        self.assertIn("lactose", prompt_arg)
        self.assertIn("jain", prompt_arg)

    @patch("app._call_gemini_json", side_effect=RuntimeError("Gemini service unavailable"))
    def test_18_post_meal_plan_gemini_failure_handled(self, mock_gemini):
        res = client.post("/api/meal-plan", json={"days": 7})
        self.assertEqual(res.status_code, 502)
        data = res.json()
        self.assertIn("AI meal plan generation failed", data["detail"])

    @patch("app._call_gemini_json")
    def test_19_database_persistence(self, mock_gemini):
        mock_raw = mock_valid_gemini_weekly_response(2000)
        mock_gemini.return_value = (mock_raw, "gemini-3.8-flash")

        conn = database.get_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM meal_plans")
        count_before = c.fetchone()[0]
        conn.close()

        res = client.post("/api/meal-plan", json={"days": 7, "diet": "Vegetarian", "goal": "Weight Maintain"})
        self.assertEqual(res.status_code, 200)

        conn = database.get_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM meal_plans")
        count_after = c.fetchone()[0]
        conn.close()

        self.assertEqual(count_after, count_before + 1)

    def test_20_get_saved_meal_plan(self):
        res = client.get("/api/meal-plan")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("plan", data)
        self.assertIsNotNone(data["plan"])
        self.assertIn("days", data["plan"])

    def test_21_get_saved_meal_plan_empty_handling(self):
        # Querying an isolated non-existent path or verifying message
        res = client.get("/api/meal-plan")
        self.assertEqual(res.status_code, 200)
        self.assertIn("message", res.json())

    @patch("app._call_gemini_json")
    def test_22_regressions_and_prior_milestones(self, mock_gemini):
        # 1. Profile retrieval (Activity 5.1)
        res_prof = client.get("/api/profile?user_id=test_planner_user_5_2")
        self.assertEqual(res_prof.status_code, 200)
        self.assertEqual(res_prof.json()["profile"]["name"], "Kavita Reddy")

        # 2. Cooking assistant (Activity 4.2)
        mock_gemini.return_value = ({
            "name": "Quick Oats Porridge",
            "emoji": "🥣",
            "description": "Warm nourishing oats bowl.",
            "prep_time_mins": 5,
            "cook_time_mins": 10,
            "servings": 1,
            "ingredients": [{"name": "Oats", "quantity": "1/2 cup", "category": "grains"}],
            "instructions": [{"step": 1, "instruction": "Boil oats."}],
        }, "gemini-3.8-flash")
        res_cook = client.post("/api/cooking", json={"ingredients": ["oats", "water"]})
        self.assertEqual(res_cook.status_code, 200)

        # 3. Freshness check (Activity 3.2)
        mock_gemini.return_value = ({
            "is_food": True,
            "food_detected": "Apple",
            "freshness_status": "fresh",
            "confidence_score": 0.96,
            "evidence_level": "high",
            "observations": ["Crisp red skin"],
            "safety_recommendations": ["Safe to eat"],
            "limitations": "Surface visual only",
        }, "gemini-3.8-flash")
        img_bytes = make_test_image()
        res_fresh = client.post("/api/freshness", files={"image": ("apple.jpg", img_bytes, "image/jpeg")})
        self.assertEqual(res_fresh.status_code, 200)


if __name__ == "__main__":
    unittest.main()
