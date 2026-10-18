"""
FoodVerse AI — Test Suite: System Integration & Edge Case Validation
Consolidates test_activity_6_1.py and test_activity_6_2.py.
"""

"""
FoodVerse AI — Smart Bridge Activity 6.1 Test Suite
Full-System Interface Integration and System Execution

Comprehensive End-to-End & Integration Tests:
  01. System Health Check: GET /api/health verifies FastAPI, OpenCV, SQLite, and module readiness.
  02. Food Recognition & Nutrition: POST /api/predict handles valid image with complete nutritional breakdown.
  03. Food Recognition Upload Validation: POST /api/predict rejects 0-byte files with HTTP 400.
  04. Food Recognition Format Validation: POST /api/predict rejects unsupported MIME types with HTTP 415.
  05. Freshness & Spoilage Detection: POST /api/freshness returns structured freshness status & safety guidance.
  06. Freshness Non-Food Handling: POST /api/freshness gracefully handles non-food uploads.
  07. Hygiene Video Monitoring: POST /api/hygiene processes video frames and returns compliance score.
  08. Hygiene Upload Validation: POST /api/hygiene rejects 0-byte or corrupted video uploads.
  09. Smart Kitchen Recipe Generation: POST /api/cooking generates structured recipes from pantry ingredients.
  10. Smart Kitchen Input Validation: POST /api/cooking rejects empty ingredient lists with HTTP 400.
  11. Smart Kitchen Vision Detection: POST /api/cooking/detect-ingredients extracts ingredients from food photo.
  12. User Profile Persistence: POST /api/profile validates biometrics, computes Mifflin-St Jeor target, and persists.
  13. User Profile Retrieval: GET /api/profile loads persisted profile or returns clean defaults for new users.
  14. User Profile Input Validation: POST /api/profile rejects out-of-range metrics with HTTP 400.
  15. Meal Plan Daily Generation: POST /api/meal-plan creates 1-day plan with daily totals & adaptive recommendations.
  16. Meal Plan Weekly Generation: POST /api/meal-plan creates 7-day plan with stored profile allergy enforcement.
  17. Meal Plan Persistence: GET /api/meal-plan retrieves the most recently persisted plan from SQLite.
  18. Real Dashboard Analytics: GET /api/dashboard/stats computes live metrics from SQLite database.
  19. Real Activity Logging: GET /api/activities returns real activity audit log entries.
  20. Error & Timeout Handling: Gracefully handles Gemini API exceptions with HTTP 502 across modules.
  21. Database Record Preservation: Confirms activity_logs, meal_plans, and user_profiles maintain integrity.
  22. CORS & Preflight Compliance: Verifies CORS headers permit frontend cross-origin requests.
"""

import io
import json
import unittest
import warnings
from unittest.mock import patch, MagicMock

import cv2
import numpy as np
from PIL import Image

warnings.filterwarnings('ignore', message=r'.*starlette\.testclient.*')

from fastapi.testclient import TestClient

import app
import database

client = TestClient(app.app)


def make_test_image(width: int = 150, height: int = 150, color: tuple = (100, 150, 200)) -> bytes:
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


_MOCK_PIL = Image.new("RGB", (200, 200), (180, 120, 60))
_MOCK_FRESHNESS_TELEMETRY = {
    "freshness_cues": {
        "color_profile": {
            "mean_saturation_pct": 50.0,
            "dominant_tone": "red",
        },
        "texture_profile": {
            "surface_uniformity": "moderate",
        },
        "quality_indicators": {
            "sharpness_score": 250.0,
            "is_blurry": False,
            "exposure_quality": "normal",
            "brightness_mean": 128.0,
        },
    },
    "preprocessing_applied": {
        "decoded": True,
        "resized": False,
    },
}


def make_test_video_bytes(num_frames: int = 10, width: int = 160, height: int = 120) -> bytes:
    """Creates a minimal in-memory MP4 test video with OpenCV."""
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(tmp_path, fourcc, 10.0, (width, height))
        for i in range(num_frames):
            frame = np.full((height, width, 3), (i * 20) % 256, dtype=np.uint8)
            writer.write(frame)
        writer.release()

        with open(tmp_path, "rb") as f:
            data = f.read()
        return data
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


class TestFullSystemIntegration(unittest.TestCase):
    """Activity 6.1 End-to-End and Cross-Module Integration Tests."""

    def test_01_system_health_check(self):
        res = client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["backend"], "FastAPI")
        self.assertIn("OpenCV", data["image_preprocessor"])
        self.assertIn("SQLite", data["database"])
        self.assertIn("active_models", data)

    @patch("app._call_gemini_json")
    def test_02_food_recognition_and_nutrition(self, mock_gemini):
        mock_gemini.return_value = ({
            "is_food": True,
            "predicted_class": "Idli Sambar",
            "confidence": "High",
            "confidence_score": 0.96,
            "confidence_note": "Steamed idlis and sambar clearly visible",
            "food_items": ["Idli", "Sambar"],
            "visual_observations": ["White fluffy rice cakes", "Lentil soup with drumsticks"],
            "nutrition": {
                "serving": "2 idlis with 1 cup sambar",
                "calories": 280,
                "protein": 8,
                "carbs": 52,
                "fat": 3,
                "fiber": 6,
                "tip": "High protein, fermented easily digestible meal."
            },
            "description": "Steamed fermented rice and lentil cakes served with vegetable stew."
        }, "gemini-3.8-flash")

        img_bytes = make_test_image()
        res = client.post("/api/predict", files={"image": ("food.jpg", img_bytes, "image/jpeg")})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["is_food"])
        self.assertEqual(data["food_name"], "Idli Sambar")
        self.assertIn("nutrition", data)
        self.assertIn(data["nutrition"]["calories"], [210, 280])
        self.assertIn("preprocessing_applied", data)
        self.assertIn("freshness_cues", data["preprocessing_applied"])

    def test_03_food_recognition_rejects_empty_upload(self):
        res = client.post("/api/predict", files={"image": ("empty.jpg", b"", "image/jpeg")})
        self.assertEqual(res.status_code, 400)
        self.assertIn("empty", res.json()["detail"].lower())

    def test_04_food_recognition_rejects_unsupported_mime(self):
        res = client.post("/api/predict", files={"image": ("notes.txt", b"not an image", "text/plain")})
        self.assertEqual(res.status_code, 415)
        self.assertIn("unsupported", res.json()["detail"].lower())

    @patch("app.preprocess_image_opencv", return_value=(_MOCK_PIL, _MOCK_FRESHNESS_TELEMETRY))
    @patch("app._call_gemini_json")
    def test_05_freshness_detection_success(self, mock_gemini, mock_prep):
        mock_gemini.return_value = ({
            "status": "fresh",
            "label": "Fresh",
            "certainty": "High",
            "food_item": "Tomato",
            "shelf": "5-7 days if refrigerated",
            "observations": {
                "color": "Vibrant red color",
                "texture": "Firm skin, no bruising",
                "defects": "No visible rot"
            },
            "checks": [
                {"ok": True, "text": "Firm skin and vibrant red color."},
                {"ok": True, "text": "No surface bruising or decay."}
            ],
            "recommendations": [
                "Store in the crisper drawer to maintain freshness.",
                "Keep away from ethylene-producing fruits."
            ],
            "disclaimer": "Visual assessment cannot detect invisible bacteria."
        }, "gemini-3.8-flash")

        img_bytes = make_test_image()
        res = client.post("/api/freshness", files={"image": ("tomato.jpg", img_bytes, "image/jpeg")})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "fresh")
        self.assertEqual(data["label"], "Fresh")
        self.assertEqual(data["food_item"], "Tomato")
        self.assertIn("observed_cues", data)
        self.assertIn("safety_recommendations", data)

    @patch("app._call_gemini_json")
    def test_06_freshness_handles_non_food(self, mock_gemini):
        mock_gemini.return_value = ({
            "status": "inconclusive",
            "label": "Inconclusive",
            "certainty": "Cautious",
            "food_item": "Plastic Bottle",
            "shelf": "Cannot determine",
            "observations": {
                "color": "Clear plastic",
                "texture": "Rigid synthetic container",
                "defects": "Non-food item detected"
            },
            "checks": [
                {"ok": False, "text": "Object is non-edible synthetic packaging."}
            ],
            "recommendations": [
                "Not an edible food item."
            ],
            "disclaimer": "Non-food item."
        }, "gemini-3.8-flash")

        img_bytes = make_test_image()
        res = client.post("/api/freshness", files={"image": ("bottle.jpg", img_bytes, "image/jpeg")})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "inconclusive")
        self.assertIn("limitations", data)

    @patch("app._call_gemini_json")
    def test_07_hygiene_video_monitoring(self, mock_gemini):
        mock_gemini.return_value = ({
            "observations": [
                {
                    "indicator": "surface_cleanliness",
                    "status": "observed",
                    "evidence": "Preparation counter clean and sanitized."
                },
                {
                    "indicator": "gloves_ppe",
                    "status": "observed",
                    "evidence": "Staff observed wearing food-grade gloves."
                },
                {
                    "indicator": "hair_coverings",
                    "status": "observed",
                    "evidence": "Staff wearing hairnets."
                }
            ],
            "frame_summary": "Kitchen staff adhere to food safety guidelines."
        }, "gemini-3.8-flash")

        video_bytes = make_test_video_bytes(num_frames=6)
        res = client.post("/api/hygiene", files={"image": ("kitchen.mp4", video_bytes, "video/mp4")})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("compliance_score", data)
        self.assertIn("score", data)
        self.assertIn("grade", data)
        self.assertEqual(data["media_type"], "video")

    def test_08_hygiene_rejects_empty_video(self):
        res = client.post("/api/hygiene", files={"image": ("empty.mp4", b"", "video/mp4")})
        self.assertEqual(res.status_code, 400)
        self.assertIn("empty", res.json()["detail"].lower())

    @patch("app._call_gemini_json")
    def test_09_smart_kitchen_recipe_generation(self, mock_gemini):
        mock_gemini.return_value = ({
            "name": "Masala Vegetable Pulao",
            "emoji": "🍚",
            "description": "Fragrant basmati rice gently cooked with spiced peas and carrots.",
            "prep_time_mins": 10,
            "cook_time_mins": 20,
            "servings": 2,
            "ingredients": [
                {"name": "Basmati rice", "quantity": "1 cup", "category": "grains"},
                {"name": "Green peas", "quantity": "1/2 cup", "category": "produce"}
            ],
            "instructions": [{"step": 1, "instruction": "Sauté spices and simmer rice."}],
            "cooking_tips": ["Soak rice for 20 minutes before cooking."],
            "food_safety_reminders": ["Serve piping hot."]
        }, "gemini-3.8-flash")

        res = client.post("/api/cooking", json={"ingredients": ["rice", "peas", "spices"]})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["name"], "Masala Vegetable Pulao")
        self.assertIn("prep_time_mins", data)
        self.assertIn("steps", data)

    def test_10_smart_kitchen_rejects_empty_ingredients(self):
        res = client.post("/api/cooking", json={"ingredients": []})
        self.assertEqual(res.status_code, 400)
        self.assertIn("ingredient", res.json()["detail"].lower())

    @patch("app._call_gemini_json")
    def test_11_smart_kitchen_detect_ingredients_from_image(self, mock_gemini):
        mock_gemini.return_value = ({
            "is_food": True,
            "detected_ingredients": ["Garlic", "Ginger", "Red Chillies"],
            "confidence": 0.95
        }, "gemini-3.8-flash")

        img_bytes = make_test_image()
        res = client.post(
            "/api/cooking/detect-ingredients",
            files={"image": ("pantry.jpg", img_bytes, "image/jpeg")}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["is_food"])
        self.assertIn("Garlic", data["detected_ingredients"])

    def test_12_user_profile_persistence(self):
        payload = {
            "user_id": "test_e2e_user_6_1",
            "name": "Meera Sen",
            "age": 27,
            "gender": "female",
            "height_cm": 164.0,
            "weight_kg": 56.0,
            "diet": "Vegetarian",
            "goal": "Weight Maintain",
            "activity_level": "moderately active",
            "budget": "Medium",
            "allergies": "peanuts",
            "intolerances": "lactose",
            "dislikes": "bitter gourd",
            "restrictions": "no beef",
        }
        res = client.post("/api/profile", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "saved")
        self.assertEqual(data["profile"]["name"], "Meera Sen")
        self.assertIn("medical_disclaimer", data["profile"])

    def test_13_user_profile_retrieval(self):
        res = client.get("/api/profile?user_id=test_e2e_user_6_1")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["is_new"])
        self.assertEqual(data["profile"]["name"], "Meera Sen")
        self.assertEqual(data["profile"]["allergies"], ["peanuts"])

    def test_14_user_profile_validation_rejects_invalid_metrics(self):
        res = client.post("/api/profile", json={"age": 140, "height_cm": 30.0})
        self.assertEqual(res.status_code, 400)
        errs = res.json()["detail"]["errors"]
        self.assertTrue(any("Age must be between 1 and 120" in e for e in errs))
        self.assertTrue(any("Height must be between 50 and 250 cm" in e for e in errs))

    @patch("app._call_gemini_json")
    def test_15_meal_plan_daily_generation(self, mock_gemini):
        mock_gemini.return_value = ({
            "plan_type": "daily",
            "target_calories": 1900,
            "nutrition_notes": "Balanced daily fuel.",
            "adaptive_recommendations": ["Eat fiber-dense breakfast."],
            "days": {
                "Today": {
                    "breakfast": {"name": "Moong Chilla", "cal": 380, "protein": 14, "carbs": 50, "fat": 8},
                    "lunch": {"name": "Dal Rice", "cal": 600, "protein": 20, "carbs": 90, "fat": 12},
                    "dinner": {"name": "Tofu Bowl", "cal": 500, "protein": 22, "carbs": 60, "fat": 14},
                    "snack": {"name": "Foxnuts", "cal": 150, "protein": 4, "carbs": 24, "fat": 3}
                }
            }
        }, "gemini-3.8-flash")

        res = client.post("/api/meal-plan", json={"user_id": "test_e2e_user_6_1", "days": 1})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["plan_type"], "daily")
        self.assertIn("Today", data["days"])

    @patch("app._call_gemini_json")
    def test_16_meal_plan_weekly_generation_with_allergy_enforcement(self, mock_gemini):
        # Gemini inadvertently includes peanut butter, which must be auto-purged
        mock_gemini.return_value = ({
            "plan_type": "weekly",
            "target_calories": 1900,
            "nutrition_notes": "Balanced weekly schedule.",
            "adaptive_recommendations": ["Keep hydrated."],
            "days": {
                "Mon": {
                    "breakfast": {
                        "name": "Peanut Toast",  # Allergen! User is allergic to peanuts
                        "cal": 400, "protein": 12, "carbs": 50, "fat": 14,
                        "ingredients": ["peanut butter", "bread"]
                    },
                    "lunch": {"name": "Dal Rice", "cal": 600, "protein": 20, "carbs": 90, "fat": 12},
                    "dinner": {"name": "Tofu Bowl", "cal": 500, "protein": 22, "carbs": 60, "fat": 14},
                    "snack": {"name": "Fruit", "cal": 150, "protein": 2, "carbs": 30, "fat": 1}
                }
            }
        }, "gemini-3.8-flash")

        res = client.post("/api/meal-plan", json={"user_id": "test_e2e_user_6_1", "days": 7})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        # Ensure breakfast was sanitized and substituted
        b = data["days"]["Mon"]["breakfast"]
        self.assertNotIn("peanut", b["name"].lower())
        self.assertIn("safety_adaptation_note", b)

    def test_17_get_saved_meal_plan_from_database(self):
        res = client.get("/api/meal-plan")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("plan", data)
        self.assertIsNotNone(data["plan"])

    def test_18_real_dashboard_analytics_from_sqlite(self):
        res = client.get("/api/dashboard/stats")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("total_meals", data)
        self.assertIn("total_scans", data)
        self.assertIn("weekly_calories", data)
        self.assertIn("macro_split", data)

    def test_19_real_activity_logs_from_sqlite(self):
        res = client.get("/api/activities?limit=10")
        self.assertEqual(res.status_code, 200)
        activities = res.json()
        self.assertIsInstance(activities, list)
        self.assertGreaterEqual(len(activities), 1)

    @patch("app._call_gemini_json", side_effect=RuntimeError("AI backend network timeout"))
    def test_20_gemini_error_propagation_http_502(self, mock_gemini):
        res = client.post("/api/cooking", json={"ingredients": ["rice", "water"]})
        self.assertEqual(res.status_code, 502)
        self.assertIn("AI", res.json()["detail"])

    def test_21_database_record_preservation(self):
        conn = database.get_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM activity_logs")
        logs = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM meal_plans")
        plans = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM user_profiles")
        profs = c.fetchone()[0]
        conn.close()

        self.assertGreaterEqual(logs, 200)
        self.assertGreaterEqual(plans, 20)
        self.assertGreaterEqual(profs, 2)

    def test_22_cors_preflight_headers(self):
        res = client.options("/api/predict", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"})
        self.assertEqual(res.status_code, 200)
        self.assertIn("access-control-allow-origin", res.headers)

#===========================================================================
# Section: test_activity_6_2.py
#===========================================================================

"""
FoodVerse AI — Smart Bridge Activity 6.2 Test Suite
Functional Testing and Edge Case Validation

Covers rigorous, edge-case scenarios across all modules:
  Group 1: Food Recognition & Nutrition Edge Cases
    01. Low-resolution image ingestion (16x16 pixels) decodes cleanly without crashes.
    02. Extreme aspect ratio (panoramic 800x40) decodes and extracts valid orientation.
    03. Corrupt file byte stream returns HTTP 400 with unreadable image notice.
    04. Non-food input strictly suppresses nutrition (nutrition=None, no fabricated calories).
    05. Unlisted dish fallback calculates deterministic 0-100 health score without reference DB match.
    06. Extreme/negative raw nutrition values are sanitized to non-negative bounds.

  Group 2: Freshness Detection Edge Cases
    07. Severely underexposed image (brightness < 40) short-circuits to inconclusive early.
    08. Severely overexposed image (brightness > 220) short-circuits to inconclusive early.
    09. Blurry image (Laplacian variance < 100) short-circuits to inconclusive early.
    10. All four canonical statuses (fresh, moderately_fresh, spoiled, inconclusive) provide tailored guidance.
    11. Visual analysis limitations & disclaimer are always present and never guarantee food safety.
    12. Gemini timeout/failure is caught and gracefully returns HTTP 200 with inconclusive status.

  Group 3: Hygiene Monitoring Edge Cases
    13. Ultra-short video clip (0.2s, 2 frames) handles frame sampling without division-by-zero.
    14. Corrupt video upload returns HTTP 400.
    15. Unsupported video format (e.g. video/x-flv) returns HTTP 415.
    16. Video with 100% uncertain indicators does not penalize score or trigger false violations.
    17. Frame extraction is capped at MAX_FRAMES (10) to prevent resource exhaustion.

  Group 4: Smart Kitchen Cooking Guidance Edge Cases
    18. Empty or whitespace-only ingredients list returns HTTP 400.
    19. Missing context fields (cuisine, skill_level, servings) safely apply beginner-friendly defaults.
    20. Non-food photo submitted to detect-ingredients returns is_food=False and empty ingredients list.
    21. Corrupt image to detect-ingredients returns HTTP 400.
    22. Incomplete Gemini recipe output is structured with fallback preparation steps and safety reminders.

  Group 5: User Profile & Meal Planner Edge Cases
    23. Exact boundary profile values (age: 1 & 120, height: 50 & 250, weight: 20 & 300) accepted (HTTP 200).
    24. Out-of-bounds profile values (age: 0/121, height: 49/251, weight: 19/301) rejected with HTTP 400.
    25. Separation of allergies vs intolerances vs dislikes vs restrictions without cross-contamination.
    26. Strict allergen exclusion: Unsafe primary dish & alternatives are purged/substituted.
    27. Lactose intolerance exclusion safely substitutes dairy dishes (e.g. Paneer Butter Masala).
    28. Missing numeric nutrients in AI response are normalized and daily totals match exact slot sums.
    29. All meal plan responses attach explicit medical disclaimer and flag estimates.
    30. Meal plan SQLite round-trip: generated plan is persisted and retrieved identically.
"""

import io
import json
import os
import tempfile
import unittest
import warnings
from unittest.mock import patch, MagicMock

import cv2
import numpy as np
from PIL import Image

warnings.filterwarnings('ignore', message=r'.*starlette\.testclient.*')

from fastapi.testclient import TestClient

import app
import cooking_service
import database
import freshness_service
import hygiene_service
import image_processor
import nutrition_service
import profile_service
import meal_planner_service
import video_processor

client = TestClient(app.app)


# ---------------------------------------------------------------------------
# Test Helpers
# ---------------------------------------------------------------------------

def make_test_image(width: int = 150, height: int = 150, color: tuple = (120, 160, 200), format: str = "JPEG") -> bytes:
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def make_test_video(num_frames: int = 6, width: int = 160, height: int = 120, fps: float = 10.0) -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(tmp_path, fourcc, fps, (width, height))
        for i in range(num_frames):
            frame = np.full((height, width, 3), (i * 30) % 256, dtype=np.uint8)
            writer.write(frame)
        writer.release()

        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


_STABLE_PIL = Image.new("RGB", (200, 200), (180, 120, 60))
_STABLE_TELEMETRY = {
    "freshness_cues": {
        "color_profile": {"mean_saturation_pct": 50.0, "dominant_tone": "red"},
        "texture_profile": {"surface_uniformity": "moderate"},
        "quality_indicators": {
            "sharpness_score": 250.0,
            "is_blurry": False,
            "exposure_quality": "normal",
            "brightness_mean": 128.0,
        },
    },
    "preprocessing_applied": {"decoded": True, "resized": False},
}


class TestActivity62EdgeCaseValidation(unittest.TestCase):
    """Activity 6.2 Rigorous Functional and Edge-Case Test Suite."""

    # =========================================================================
    # Group 1: Food Recognition & Nutrition Edge Cases
    # =========================================================================

    def test_01_food_rec_low_resolution_image(self):
        """Very small 16x16 pixel image decodes without crashing and provides valid telemetry."""
        raw = make_test_image(width=16, height=16)
        pil, tele = app.preprocess_image_opencv(raw)
        self.assertIsInstance(pil, Image.Image)
        self.assertEqual(pil.size, (16, 16))
        self.assertEqual(tele["original_dimensions"], [16, 16])
        self.assertFalse(tele["resized"])

    def test_02_food_rec_extreme_aspect_ratio_panoramic(self):
        """Extreme aspect ratio (800x40 = 20:1) decodes correctly and classifies orientation."""
        raw = make_test_image(width=800, height=40)
        pil, tele = app.preprocess_image_opencv(raw)
        self.assertEqual(pil.size, (800, 40))
        self.assertEqual(tele["orientation"], "landscape")
        self.assertEqual(tele["aspect_ratio"], 20.0)

    def test_03_food_rec_corrupt_file_bytes(self):
        """Random unparseable bytes return HTTP 400 with helpful error detail."""
        corrupt_bytes = b"NOT_A_VALID_JPEG_HEADER_CORRUPT_BYTES_XYZ"
        res = client.post("/api/predict", files={"image": ("corrupt.jpg", corrupt_bytes, "image/jpeg")})
        self.assertEqual(res.status_code, 400)
        self.assertIn("corrupt", res.json()["detail"].lower())

    @patch("app._call_gemini_json")
    def test_04_food_rec_non_food_object_suppresses_nutrition(self, mock_gemini):
        """Non-food object suppresses nutrition completely (nutrition=None, no fabricated calories)."""
        mock_gemini.return_value = ({
            "is_food": False,
            "predicted_class": "Unrecognized Non-Food Object",
            "description": "Metal kitchen scissors resting on a wooden board.",
            "confidence": "Low",
            "confidence_score": 0.15,
            "confidence_note": "No edible food items identified in the frame.",
            "food_items": [],
            "visual_observations": ["Metallic blades", "Black plastic handles"],
            "nutrition": None
        }, "gemini-3.8-flash")

        raw = make_test_image()
        res = client.post("/api/predict", files={"image": ("scissors.jpg", raw, "image/jpeg")})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["is_food"])
        self.assertIsNone(data["nutrition"])
        self.assertEqual(data["food_name"], "Unrecognized Non-Food Object")
        self.assertEqual(data["confidence"], "Low")

    def test_05_food_rec_unlisted_dish_deterministic_fallback(self):
        """Dish not present in ICMR-NIN database uses sanitized AI values and computes health score."""
        raw_gemini_nutrition = {
            "calories": 420,
            "protein": 14,
            "carbs": 60,
            "fat": 12,
            "fiber": 8,
            "serving": "1 large bowl (300g)",
            "tip": "Rich in dietary fiber and complex carbohydrates."
        }
        nut = nutrition_service.estimate_nutrition_and_score(
            food_name="Exotic Dragonfruit Chia Bowl",
            food_items=["Dragonfruit", "Chia seeds", "Almond milk"],
            gemini_raw_nutrition=raw_gemini_nutrition,
            is_food=True
        )
        self.assertIsNotNone(nut)
        self.assertEqual(nut["calories"], 420)
        self.assertIn("health_score", nut)
        self.assertGreaterEqual(nut["health_score"], 0)
        self.assertLessEqual(nut["health_score"], 100)
        self.assertEqual(nut["estimation_method"], "ai_visual_estimation")

    def test_06_food_rec_extreme_nutrition_bounds(self):
        """Extreme or non-numeric values in raw nutrition are sanitized to safe bounds."""
        val = nutrition_service.sanitize_nutrient_value(-100, default=0.0)
        self.assertEqual(val, 0.0)

        val_nan = nutrition_service.sanitize_nutrient_value(float("nan"), default=0.0)
        self.assertEqual(val_nan, 0.0)

        cleaned, status = nutrition_service.validate_and_balance_nutrition({
            "calories": -40,
            "protein": 10.0,
            "carbs": 20.0,
            "fat": 5.0,
        })
        self.assertEqual(cleaned["calories"], 165)  # Re-derived from 4*10 + 4*20 + 9*5

    # =========================================================================
    # Group 2: Freshness Detection Edge Cases
    # =========================================================================

    def test_07_freshness_severely_underexposed_image(self):
        """Underexposed image (brightness < 40) short-circuits to inconclusive without calling Gemini."""
        dark_cues = {
            "quality_indicators": {
                "sharpness_score": 200.0,
                "is_blurry": False,
                "exposure_quality": "underexposed",
                "brightness_mean": 25.0,
            }
        }
        res = freshness_service.classify_freshness(freshness_cues=dark_cues, gemini_data=None)
        self.assertEqual(res["status"], "inconclusive")
        self.assertEqual(res["assessment_method"], "inconclusive_image_quality")
        self.assertEqual(res["evidence_level"], "insufficient")
        self.assertTrue(any("exposure" in cue.lower() for cue in res["observed_cues"]))

    def test_08_freshness_severely_overexposed_image(self):
        """Overexposed image (brightness > 220) short-circuits to inconclusive."""
        bright_cues = {
            "quality_indicators": {
                "sharpness_score": 200.0,
                "is_blurry": False,
                "exposure_quality": "overexposed",
                "brightness_mean": 240.0,
            }
        }
        res = freshness_service.classify_freshness(freshness_cues=bright_cues, gemini_data=None)
        self.assertEqual(res["status"], "inconclusive")
        self.assertEqual(res["assessment_method"], "inconclusive_image_quality")

    def test_09_freshness_severely_blurry_image(self):
        """Blurry image (is_blurry=True) short-circuits to inconclusive with insufficient evidence."""
        blurry_cues = {
            "quality_indicators": {
                "sharpness_score": 15.0,
                "is_blurry": True,
                "exposure_quality": "normal",
                "brightness_mean": 128.0,
            }
        }
        res = freshness_service.classify_freshness(freshness_cues=blurry_cues, gemini_data=None)
        self.assertEqual(res["status"], "inconclusive")
        self.assertEqual(res["evidence_level"], "insufficient")
        self.assertTrue(any("blurry" in cue.lower() for cue in res["observed_cues"]))

    def test_10_freshness_all_four_canonical_statuses(self):
        """classify_freshness handles fresh, aging, spoiled, and unexpected gracefully."""
        cues = _STABLE_TELEMETRY["freshness_cues"]

        # 1. Fresh
        r_fresh = freshness_service.classify_freshness(cues, {"status": "fresh", "label": "Fresh", "certainty": "High", "food_item": "Apple"})
        self.assertEqual(r_fresh["status"], "fresh")
        self.assertEqual(r_fresh["label"], "Fresh")

        # 2. Moderately Fresh (aging)
        r_mod = freshness_service.classify_freshness(cues, {"status": "aging", "label": "Use Soon", "certainty": "Medium", "food_item": "Spinach"})
        self.assertEqual(r_mod["status"], "moderately_fresh")
        self.assertEqual(r_mod["label"], "Use Soon")

        # 3. Spoiled
        r_spoil = freshness_service.classify_freshness(cues, {"status": "spoiled", "label": "Potential Spoilage", "certainty": "High", "food_item": "Bread"})
        self.assertEqual(r_spoil["status"], "spoiled")
        self.assertEqual(r_spoil["label"], "Potential Spoilage")

        # 4. Unknown string -> inconclusive
        r_unk = freshness_service.classify_freshness(cues, {"status": "alien_status", "label": "?", "certainty": "Low", "food_item": "Unknown"})
        self.assertEqual(r_unk["status"], "inconclusive")

    def test_11_freshness_disclaimer_and_limitations_always_present(self):
        """All freshness outputs must include non-empty limitations and disclaimer notices."""
        cues = _STABLE_TELEMETRY["freshness_cues"]
        res = freshness_service.classify_freshness(cues, None)
        self.assertIn("limitations", res)
        self.assertIn("disclaimer", res)
        self.assertIn("cannot detect", res["limitations"].lower())

    @patch("app.preprocess_image_opencv", return_value=(_STABLE_PIL, _STABLE_TELEMETRY))
    @patch("app._call_gemini_json", side_effect=RuntimeError("AI Vision service timed out"))
    def test_12_freshness_gemini_timeout_or_error_graceful(self, mock_gemini, mock_prep):
        """When Gemini fails or times out, /api/freshness returns HTTP 200 with inconclusive status."""
        raw = make_test_image()
        res = client.post("/api/freshness", files={"image": ("apple.jpg", raw, "image/jpeg")})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "inconclusive")
        self.assertEqual(data["assessment_method"], "inconclusive_gemini_failure")

    # =========================================================================
    # Group 3: Hygiene Monitoring Edge Cases
    # =========================================================================

    @patch("app._call_gemini_json")
    def test_13_hygiene_short_video_clip(self, mock_gemini):
        """A minimal 2-frame video clip decodes safely and completes hygiene scoring."""
        mock_gemini.return_value = ({
            "observations": [
                {"indicator": "surface_cleanliness", "status": "observed", "evidence": "Clean counter surface"}
            ],
            "frame_summary": "Clean prep area"
        }, "gemini-3.8-flash")

        video_bytes = make_test_video(num_frames=2, fps=10.0)  # 0.2s duration
        res = client.post("/api/hygiene", files={"image": ("short.mp4", video_bytes, "video/mp4")})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["media_type"], "video")
        self.assertGreaterEqual(data["compliance_score"], 0)

    def test_14_hygiene_corrupt_video_upload(self):
        """Corrupt byte payload with video/mp4 MIME type returns HTTP 400."""
        res = client.post("/api/hygiene", files={"image": ("bad.mp4", b"NOT_A_VALID_MP4_VIDEO", "video/mp4")})
        self.assertEqual(res.status_code, 400)
        self.assertIn("video", res.json()["detail"].lower())

    def test_15_hygiene_unsupported_video_mime(self):
        """Unsupported video MIME type (video/x-flv) returns HTTP 415."""
        res = client.post("/api/hygiene", files={"image": ("clip.flv", b"flv_data", "video/x-flv")})
        self.assertEqual(res.status_code, 415)
        self.assertIn("unsupported", res.json()["detail"].lower())

    def test_16_hygiene_uncertain_indicators_not_penalized(self):
        """When all observations are uncertain, score reflects assessable coverage without unfair penalty."""
        obs = [
            {"indicator": "surface_cleanliness", "status": "uncertain", "evidence": "Dark area"},
            {"indicator": "gloves_ppe", "status": "uncertain", "evidence": "Hands obscured"},
        ]
        result = hygiene_service.calculate_compliance_score(obs)
        self.assertEqual(result["assessable_indicators"], 0)
        self.assertEqual(result["compliance_score"], 0)
        self.assertEqual(result["coverage"], 0.0)
        self.assertEqual(len(result["alerts"]), 0)  # No false alerts generated for uncertainty

    def test_17_hygiene_frame_extraction_cap(self):
        """Video lasting longer than interval creates frames capped strictly at MAX_FRAMES."""
        # 30 frames at 10fps = 3.0s, with interval 0.2s would try to sample 15 frames, capped at 10
        video_bytes = make_test_video(num_frames=30, fps=10.0)
        frames, tele = video_processor.extract_frames(
            raw_bytes=video_bytes,
            content_type="video/mp4",
            interval_s=0.2,
            max_frames=5
        )
        self.assertLessEqual(len(frames), 5)
        self.assertEqual(tele["sampled_count"], len(frames))

    # =========================================================================
    # Group 4: Smart Kitchen Cooking Guidance Edge Cases
    # =========================================================================

    def test_18_cooking_empty_or_whitespace_ingredients(self):
        """Providing only whitespace or empty strings returns HTTP 400."""
        res = client.post("/api/cooking", json={"ingredients": ["  ", "\t", ""]})
        self.assertEqual(res.status_code, 400)
        self.assertIn("ingredient", res.json()["detail"].lower())

    @patch("app._call_gemini_json")
    def test_19_cooking_missing_context_uses_safe_defaults(self, mock_gemini):
        """Omitting optional context defaults safely to Beginner, Indian, 2 servings."""
        mock_gemini.return_value = ({
            "name": "Quick Jeera Rice",
            "emoji": "🍚",
            "description": "Simple fragrant cumin-flavored basmati rice.",
            "prep_time_mins": 5,
            "cook_time_mins": 15,
            "servings": 2,
            "diet": "vegetarian",
            "cuisine": "Indian",
            "skill_level": "Beginner",
            "calories": 250,
            "ingredients": [{"name": "Basmati rice", "quantity": "1 cup"}, {"name": "Cumin seeds", "quantity": "1 tsp"}],
            "steps": ["Wash rice", "Heat ghee", "Add cumin", "Cook rice"],
            "cooking_tips": ["Rinse rice to remove excess starch."],
            "food_safety_reminders": ["Refrigerate leftover rice promptly."]
        }, "gemini-3.8-flash")

        res = client.post("/api/cooking", json={"ingredients": ["rice", "cumin"]})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["cuisine"], "Indian")
        self.assertEqual(data["skill_level"], "Beginner")
        self.assertEqual(data["servings"], 2)

    @patch("app._call_gemini_json")
    def test_20_cooking_detect_ingredients_non_food_image(self, mock_gemini):
        """Non-food photo submitted to detect-ingredients returns is_food=False and empty ingredients."""
        mock_gemini.return_value = ({
            "is_food": False,
            "detected_ingredients": [],
            "observations": "No culinary ingredients detected; only office supplies visible.",
            "confidence_note": "Visual analysis found non-food objects."
        }, "gemini-3.8-flash")

        raw = make_test_image()
        res = client.post("/api/cooking/detect-ingredients", files={"image": ("desk.jpg", raw, "image/jpeg")})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["is_food"])
        self.assertEqual(data["detected_ingredients"], [])

    def test_21_cooking_detect_ingredients_corrupt_upload(self):
        """Corrupt image to /api/cooking/detect-ingredients returns HTTP 400."""
        res = client.post(
            "/api/cooking/detect-ingredients",
            files={"image": ("bad.jpg", b"NOT_A_VALID_IMAGE_DATA", "image/jpeg")}
        )
        self.assertEqual(res.status_code, 400)

    def test_22_cooking_malformed_gemini_json_structured_fallback(self):
        """Malformed Gemini response missing steps & ingredients is supplemented by normalizer."""
        malformed_raw = {"name": "Experimental Stir Fry"}  # Missing ingredients, steps, timings
        norm = cooking_service.normalize_recipe_response(malformed_raw, requested_servings=3, requested_diet="Vegan")
        self.assertEqual(norm["servings"], 3)
        self.assertGreaterEqual(len(norm["steps"]), 1)
        self.assertGreaterEqual(len(norm["food_safety_reminders"]), 1)
        self.assertGreaterEqual(len(norm["cooking_tips"]), 1)

    # =========================================================================
    # Group 5: User Profile & Meal Planner Edge Cases
    # =========================================================================

    def test_23_profile_exact_boundary_metrics(self):
        """Exact valid lower and upper boundary metrics must be accepted (HTTP 200)."""
        # Exact lower boundary
        res_low = client.post("/api/profile", json={
            "user_id": "test_bound_low",
            "age": 1,
            "height_cm": 50.0,
            "weight_kg": 20.0,
            "diet": "Vegetarian",
            "goal": "Balanced Eating"
        })
        self.assertEqual(res_low.status_code, 200)
        self.assertEqual(res_low.json()["profile"]["age"], 1)

        # Exact upper boundary
        res_high = client.post("/api/profile", json={
            "user_id": "test_bound_high",
            "age": 120,
            "height_cm": 250.0,
            "weight_kg": 300.0,
            "diet": "Vegetarian",
            "goal": "Balanced Eating"
        })
        self.assertEqual(res_high.status_code, 200)
        self.assertEqual(res_high.json()["profile"]["age"], 120)

    def test_24_profile_out_of_bounds_metrics_rejected(self):
        """Out of bounds metrics (e.g. age 0 or 121, weight 19 or 301) return HTTP 400."""
        # Age 0
        r1 = client.post("/api/profile", json={"age": 0})
        self.assertEqual(r1.status_code, 400)
        self.assertTrue(any("Age" in e for e in r1.json()["detail"]["errors"]))

        # Height 49 cm
        r2 = client.post("/api/profile", json={"height_cm": 49.0})
        self.assertEqual(r2.status_code, 400)
        self.assertTrue(any("Height" in e for e in r2.json()["detail"]["errors"]))

        # Weight 301 kg
        r3 = client.post("/api/profile", json={"weight_kg": 301.0})
        self.assertEqual(r3.status_code, 400)
        self.assertTrue(any("Weight" in e for e in r3.json()["detail"]["errors"]))

    def test_25_profile_separation_allergies_intolerances_dislikes(self):
        """Allergies, intolerances, dislikes, and restrictions are distinct and never mixed."""
        payload = {
            "user_id": "test_partition_user",
            "allergies": "peanuts, shellfish",
            "intolerances": "lactose, gluten",
            "dislikes": "bitter gourd, okra",
            "restrictions": "no beef, no alcohol"
        }
        res = client.post("/api/profile", json=payload)
        self.assertEqual(res.status_code, 200)
        p = res.json()["profile"]
        self.assertEqual(set(p["allergies"]), {"peanuts", "shellfish"})
        self.assertEqual(set(p["intolerances"]), {"lactose", "gluten"})
        self.assertEqual(set(p["dislikes"]), {"bitter gourd", "okra"})
        self.assertEqual(set(p["restrictions"]), {"no beef", "no alcohol"})

    def test_26_meal_plan_allergen_substitution_and_alternative_purge(self):
        """Allergen in primary meal is replaced with safe dish; unsafe alternatives are purged."""
        user_profile = {
            "allergies": ["peanuts", "tree nuts"],
            "intolerances": [],
            "dislikes": [],
            "restrictions": [],
            "diet": "Vegetarian",
            "goal": "Weight Maintain",
            "target_calories": 1900
        }

        raw_meal = {
            "name": "Peanut Butter & Banana Toast",  # Allergen!
            "cal": 420, "protein": 12, "carbs": 50, "fat": 16,
            "ingredients": ["bread", "peanut butter", "banana"],
            "alternatives": [
                {"name": "Almond Butter Porridge", "cal": 400},  # Tree nut allergen!
                {"name": "Plain Moong Dal Chilla", "cal": 350, "protein": 14, "carbs": 48, "fat": 7}  # Safe!
            ]
        }

        normalized = meal_planner_service.normalize_meal_item(
            raw_meal=raw_meal,
            slot_name="breakfast",
            user_profile=user_profile,
            diet="Vegetarian",
            budget="Medium"
        )

        # Primary meal should have been replaced
        self.assertNotIn("peanut", normalized["name"].lower())
        self.assertIn("safety_adaptation_note", normalized)
        # Unsafe alternative (Almond) should have been purged
        alt_names = [a["name"].lower() for a in normalized.get("alternatives", [])]
        self.assertFalse(any("almond" in a for a in alt_names))

    def test_27_meal_plan_lactose_intolerance_handling(self):
        """User with lactose intolerance has dairy dishes safely substituted."""
        user_profile = {
            "allergies": [],
            "intolerances": ["lactose"],
            "dislikes": [],
            "restrictions": [],
            "diet": "Vegetarian",
            "goal": "Balanced Eating",
            "target_calories": 1900
        }

        safe_test, reason = profile_service.is_ingredient_safe_for_user("Paneer Butter Masala", user_profile)
        self.assertFalse(safe_test)
        self.assertIn("lactose", reason.lower())

        raw_meal = {
            "name": "Paneer Butter Masala with Roti",
            "cal": 650, "protein": 22, "carbs": 60, "fat": 32,
            "ingredients": ["paneer", "butter", "cream", "tomatoes"],
            "alternatives": []
        }

        normalized = meal_planner_service.normalize_meal_item(
            raw_meal=raw_meal,
            slot_name="dinner",
            user_profile=user_profile,
            diet="Vegetarian",
            budget="Medium"
        )
        self.assertNotIn("paneer", normalized["name"].lower())
        self.assertIn("safety_adaptation_note", normalized)

    def test_28_meal_plan_nutrition_normalization_and_totals_consistency(self):
        """Missing nutrient values in AI meal plan are safely bounded and daily totals match slot sums."""
        user_profile = {"allergies": [], "intolerances": [], "dislikes": [], "restrictions": []}
        raw_day = {
            "breakfast": {"name": "Poha", "cal": "not_an_int", "protein": None},
            "lunch": {"name": "Khichdi", "cal": 450, "protein": 15, "carbs": 70, "fat": 10},
            "dinner": {"name": "Soup", "cal": 250, "protein": 8, "carbs": 30, "fat": 5},
            "snack": {"name": "Nuts", "cal": 150, "protein": 4, "carbs": 10, "fat": 10}
        }

        plan = meal_planner_service.normalize_meal_plan_response(
            raw_data={"days": {"Today": raw_day}},
            user_profile=user_profile,
            diet="Vegetarian",
            goal="Weight Maintain",
            budget="Medium",
            days_count=1,
            target_cal=1800
        )

        today = plan["days"]["Today"]
        calculated_cal_sum = sum(today[slot]["cal"] for slot in meal_planner_service.SLOTS)
        self.assertEqual(today["day_summary"]["total_calories"], calculated_cal_sum)
        self.assertGreater(today["day_summary"]["total_calories"], 0)

    def test_29_meal_plan_disclaimer_and_educational_labeling(self):
        """Meal plan includes required non-medical disclaimer and marks estimates."""
        user_profile = {"allergies": [], "intolerances": [], "dislikes": [], "restrictions": []}
        plan = meal_planner_service.normalize_meal_plan_response(
            raw_data={},
            user_profile=user_profile,
            diet="Vegetarian",
            goal="Weight Maintain",
            budget="Medium",
            days_count=1,
            target_cal=1900
        )
        self.assertIn("medical_disclaimer", plan)
        self.assertIn("not constitute clinical diagnosis", plan["medical_disclaimer"].lower())
        self.assertTrue(plan["days"]["Today"]["breakfast"]["is_estimated"])

    @patch("app._call_gemini_json")
    def test_30_meal_plan_persistence_and_retrieval_integrity(self, mock_gemini):
        """Meal plan is persisted to SQLite and subsequent GET /api/meal-plan retrieves it."""
        mock_gemini.return_value = ({
            "plan_type": "daily",
            "target_calories": 2000,
            "nutrition_notes": "Fuel for active lifestyle.",
            "adaptive_recommendations": ["Eat balanced meals."],
            "days": {
                "Today": {
                    "breakfast": {"name": "Oatmeal", "cal": 350, "protein": 10, "carbs": 60, "fat": 6},
                    "lunch": {"name": "Dal Roti", "cal": 600, "protein": 20, "carbs": 85, "fat": 12},
                    "dinner": {"name": "Veg Curry", "cal": 500, "protein": 18, "carbs": 65, "fat": 14},
                    "snack": {"name": "Sprouts", "cal": 150, "protein": 8, "carbs": 25, "fat": 2}
                }
            }
        }, "gemini-3.8-flash")

        res_post = client.post("/api/meal-plan", json={"user_id": "test_e2e_edge_6_2", "days": 1})
        self.assertEqual(res_post.status_code, 200)

        res_get = client.get("/api/meal-plan")
        self.assertEqual(res_get.status_code, 200)
        saved = res_get.json()
        self.assertIsNotNone(saved["plan"])
        self.assertIn("Today", saved["plan"]["days"])


if __name__ == "__main__":
    unittest.main()
