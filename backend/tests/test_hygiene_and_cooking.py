"""
FoodVerse AI — Test Suite: Hygiene Monitoring & Smart Cooking Assistant
Consolidates test_activity_4_1.py and test_activity_4_2.py.
"""

"""
FoodVerse AI — Smart Bridge Activity 4.1 Test Suite
Restaurant Hygiene Detection and Compliance Scoring

Tests:
  01. extract_frames: valid synthetic MP4 video extracts frames with timestamps and telemetry.
  02. extract_frames: empty (0-byte) video input returns HTTP 400.
  03. extract_frames: oversized video (>50MB) returns HTTP 413.
  04. extract_frames: unsupported video MIME type returns HTTP 415.
  05. extract_frames: corrupt/unreadable bytes returns HTTP 400.
  06. extract_frames: max_frames capping works as expected.
  07. extract_frames: aspect ratio is preserved during frame resizing.
  08. parse_frame_observations: valid Gemini observation output parses into canonical structure.
  09. parse_frame_observations: invalid or unknown indicator status normalizes to 'uncertain'.
  10. parse_frame_observations: None or malformed Gemini response produces empty observations list safely.
  11. calculate_compliance_score: all observed indicators yields 100% score and 1.0 coverage.
  12. calculate_compliance_score: all not_observed indicators yields 0 score, generating alerts with severities.
  13. calculate_compliance_score: uncertain indicators are excluded from score arithmetic.
  14. calculate_compliance_score: multi-frame worst-case aggregation selects not_observed over observed.
  15. calculate_compliance_score: coverage calculated accurately based on assessable indicators weight.
  16. calculate_compliance_score: limitations and disclaimer are always present and non-empty.
  17. build_hygiene_result: contains all required Activity 4.1 keys and legacy backward-compat keys.
  18. POST /api/hygiene: image upload returns HTTP 200 with complete compliance payload.
  19. POST /api/hygiene: video upload extracts frames, queries model, and returns HTTP 200 with video telemetry.
  20. POST /api/hygiene: unsupported file type returns HTTP 415.
  21. POST /api/hygiene: Gemini failure handles gracefully and returns advisory compliance result.
  22. Regressions check: POST /api/predict (2.1), /api/freshness (3.2) remain fully functional.
"""

import io
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
import hygiene_service
import video_processor

client = TestClient(app.app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_synthetic_mp4(num_frames: int = 30, fps: float = 10.0, width: int = 320, height: int = 240) -> bytes:
    """Create a minimal valid MP4 video in memory using OpenCV VideoWriter."""
    fd, path = tempfile.mkstemp(suffix=".mp4")
    os.close(fd)
    try:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(path, fourcc, fps, (width, height))
        for i in range(num_frames):
            # Vary colors so frames are distinct
            color = (int((i * 8) % 255), int((i * 15) % 255), 100)
            frame = np.full((height, width, 3), color, dtype=np.uint8)
            cv2.putText(frame, f"Frame {i}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            out.write(frame)
        out.release()
        with open(path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass


def make_test_jpeg(width: int = 200, height: int = 200) -> bytes:
    img = Image.new("RGB", (width, height), (150, 150, 150))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def mock_gemini_hygiene_response(surface_ok: bool = True, gloves_ok: bool = True) -> dict:
    return {
        "observations": [
            {
                "indicator": "surface_cleanliness",
                "status": "observed" if surface_ok else "not_observed",
                "evidence": "Preparation counter clean and sanitized." if surface_ok else "Visible grease and residue on prep counter.",
            },
            {
                "indicator": "food_handling_practices",
                "status": "observed",
                "evidence": "Separation of raw and ready-to-eat ingredients observed.",
            },
            {
                "indicator": "cross_contamination_risk",
                "status": "observed",
                "evidence": "Color-coded cutting boards in use.",
            },
            {
                "indicator": "gloves_ppe",
                "status": "observed" if gloves_ok else "not_observed",
                "evidence": "Staff observed wearing food-grade gloves." if gloves_ok else "Staff handling food bare-handed.",
            },
            {
                "indicator": "hair_coverings",
                "status": "uncertain",
                "evidence": "Head area not visible in frame.",
            },
            {
                "indicator": "waste_management",
                "status": "observed",
                "evidence": "Lidded waste bin positioned away from prep area.",
            },
        ],
        "frame_summary": "Overall kitchen sanitation is satisfactory with minor areas to monitor.",
    }


# ---------------------------------------------------------------------------
# Unit tests: video_processor
# ---------------------------------------------------------------------------

class TestVideoProcessor(unittest.TestCase):

    def test_01_extract_frames_valid(self):
        video_bytes = create_synthetic_mp4(num_frames=30, fps=10.0)
        frames, tele = video_processor.extract_frames(
            raw_bytes=video_bytes,
            content_type="video/mp4",
            interval_s=1.0,
            max_frames=5,
        )
        self.assertIsInstance(frames, list)
        self.assertGreater(len(frames), 0)
        self.assertLessEqual(len(frames), 5)
        self.assertIn("duration_s", tele)
        self.assertIn("fps", tele)
        self.assertIn("sampled_count", tele)
        self.assertEqual(tele["sampled_count"], len(frames))
        ts, img = frames[0]
        self.assertIsInstance(ts, float)
        self.assertIsInstance(img, Image.Image)

    def test_02_extract_frames_empty(self):
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as cm:
            video_processor.extract_frames(b"", "video/mp4")
        self.assertEqual(cm.exception.status_code, 400)

    def test_03_extract_frames_oversized(self):
        from fastapi import HTTPException
        huge_bytes = b"x" * (video_processor.MAX_VIDEO_BYTES + 10)
        with self.assertRaises(HTTPException) as cm:
            video_processor.extract_frames(huge_bytes, "video/mp4")
        self.assertEqual(cm.exception.status_code, 413)

    def test_04_extract_frames_unsupported_mime(self):
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as cm:
            video_processor.extract_frames(b"dummy", "video/flv")
        self.assertEqual(cm.exception.status_code, 415)

    def test_05_extract_frames_corrupt_bytes(self):
        from fastapi import HTTPException
        corrupt_bytes = b"corrupt-data-not-a-video-stream-header"
        with self.assertRaises(HTTPException) as cm:
            video_processor.extract_frames(corrupt_bytes, "video/mp4")
        self.assertEqual(cm.exception.status_code, 400)

    def test_06_extract_frames_max_cap(self):
        video_bytes = create_synthetic_mp4(num_frames=50, fps=10.0)
        frames, tele = video_processor.extract_frames(
            raw_bytes=video_bytes,
            content_type="video/mp4",
            interval_s=0.2,
            max_frames=3,
        )
        self.assertEqual(len(frames), 3)

    def test_07_extract_frames_resize_aspect(self):
        video_bytes = create_synthetic_mp4(num_frames=10, fps=10.0, width=400, height=200)
        frames, _ = video_processor.extract_frames(
            raw_bytes=video_bytes,
            content_type="video/mp4",
            resize_max_dim=100,
        )
        _, img = frames[0]
        w, h = img.size
        self.assertLessEqual(max(w, h), 100)
        self.assertAlmostEqual(w / h, 2.0, delta=0.1)


# ---------------------------------------------------------------------------
# Unit tests: hygiene_service
# ---------------------------------------------------------------------------

class TestHygieneService(unittest.TestCase):

    def test_08_parse_frame_observations(self):
        data = mock_gemini_hygiene_response()
        parsed = hygiene_service.parse_frame_observations(data, frame_timestamp=1.5)
        self.assertEqual(len(parsed), 6)
        first = parsed[0]
        self.assertEqual(first["indicator"], "surface_cleanliness")
        self.assertEqual(first["status"], "observed")
        self.assertEqual(first["frame_timestamp"], 1.5)
        self.assertIn("label", first)

    def test_09_parse_frame_observations_status_fallback(self):
        data = {
            "observations": [
                {"indicator": "gloves_ppe", "status": "non_standard_status", "evidence": "text"}
            ]
        }
        parsed = hygiene_service.parse_frame_observations(data, 0.0)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["status"], "uncertain")

    def test_10_parse_frame_observations_malformed(self):
        self.assertEqual(hygiene_service.parse_frame_observations(None, 0.0), [])
        self.assertEqual(hygiene_service.parse_frame_observations({}, 0.0), [])
        self.assertEqual(hygiene_service.parse_frame_observations({"observations": "not-a-list"}, 0.0), [])

    def test_11_calculate_compliance_score_perfect(self):
        all_obs = [
            {"indicator": k, "label": meta["label"], "status": "observed", "evidence": "Compliant", "frame_timestamp": 0.0}
            for k, meta in hygiene_service.INDICATOR_REGISTRY.items()
        ]
        res = hygiene_service.calculate_compliance_score(all_obs)
        self.assertEqual(res["compliance_score"], 100)
        self.assertEqual(res["coverage"], 1.0)
        self.assertEqual(res["assessable_indicators"], 6)
        self.assertEqual(len(res["alerts"]), 0)

    def test_12_calculate_compliance_score_all_deficits(self):
        all_obs = [
            {"indicator": k, "label": meta["label"], "status": "not_observed", "evidence": "Violation", "frame_timestamp": 1.0}
            for k, meta in hygiene_service.INDICATOR_REGISTRY.items()
        ]
        res = hygiene_service.calculate_compliance_score(all_obs)
        self.assertEqual(res["compliance_score"], 0)
        self.assertEqual(res["coverage"], 1.0)
        self.assertEqual(len(res["alerts"]), 6)
        # Verify alert contains severity and action
        alert0 = res["alerts"][0]
        self.assertIn("severity", alert0)
        self.assertIn("action", alert0)

    def test_13_calculate_compliance_score_uncertain_excluded(self):
        # 1 observed (surface: 25pts), 1 not_observed (gloves: 15pts), rest uncertain
        all_obs = [
            {"indicator": "surface_cleanliness", "label": "Surface", "status": "observed", "evidence": "Clean", "frame_timestamp": 0.0},
            {"indicator": "gloves_ppe", "label": "Gloves", "status": "not_observed", "evidence": "Missing", "frame_timestamp": 0.0},
            {"indicator": "hair_coverings", "label": "Hair", "status": "uncertain", "evidence": "Unclear", "frame_timestamp": 0.0},
        ]
        res = hygiene_service.calculate_compliance_score(all_obs)
        # Assessable weight = 25 + 15 = 40. Retained = 25. Score = 25/40 * 100 = 62.5 -> 62 (banker's rounding)
        self.assertEqual(res["assessable_indicators"], 2)
        self.assertEqual(res["compliance_score"], 62)
        self.assertAlmostEqual(res["coverage"], 40 / 100.0, delta=0.01)
        self.assertEqual(len(res["uncertain_indicators"]), 4)  # 1 explicit uncertain + 3 not in frame

    def test_14_calculate_compliance_score_worst_case_aggregation(self):
        # Frame 1: observed, Frame 2: not_observed for the same indicator
        all_obs = [
            {"indicator": "surface_cleanliness", "label": "Surface", "status": "observed", "evidence": "Looks fine", "frame_timestamp": 0.0},
            {"indicator": "surface_cleanliness", "label": "Surface", "status": "not_observed", "evidence": "Spill seen", "frame_timestamp": 3.0},
        ]
        res = hygiene_service.calculate_compliance_score(all_obs)
        # Surface cleanliness should evaluate to not_observed (0 retained points)
        self.assertEqual(res["compliance_score"], 0)
        self.assertEqual(len(res["alerts"]), 1)
        self.assertEqual(res["alerts"][0]["timestamp_s"], 3.0)

    def test_15_coverage_calculation(self):
        all_obs = [
            {"indicator": "surface_cleanliness", "label": "Surface", "status": "observed", "evidence": "Clean", "frame_timestamp": 0.0},
        ]
        res = hygiene_service.calculate_compliance_score(all_obs)
        # Surface weight is 25 / 100
        self.assertAlmostEqual(res["coverage"], 0.25, delta=0.01)

    def test_16_limitations_and_disclaimer_present(self):
        res = hygiene_service.calculate_compliance_score([])
        self.assertTrue(bool(res["limitations"]))
        self.assertTrue(bool(res["disclaimer"]))

    def test_17_build_hygiene_result_keys(self):
        score_res = hygiene_service.calculate_compliance_score([])
        built = hygiene_service.build_hygiene_result(
            score_result=score_res,
            all_observations=[],
            frames_telemetry={"duration_s": 5.0},
            gemini_model_used="gemini-test",
            media_type="video",
        )
        canonical_keys = {
            "compliance_score", "assessable_indicators", "total_indicators",
            "coverage", "score_breakdown", "alerts", "uncertain_indicators",
            "observations", "media_type", "frames_telemetry", "limitations",
        }
        legacy_keys = {"score", "grade", "rubric_explanation", "summary", "findings", "actionable_corrections", "disclaimer", "engine"}
        self.assertTrue(canonical_keys.issubset(built.keys()))
        self.assertTrue(legacy_keys.issubset(built.keys()))
        self.assertEqual(built["media_type"], "video")


# ---------------------------------------------------------------------------
# Integration tests: POST /api/hygiene via TestClient
# ---------------------------------------------------------------------------

class TestHygieneAPIIntegration(unittest.TestCase):

    @patch("app._call_gemini_json", return_value=(mock_gemini_hygiene_response(), "gemini-3.8-flash"))
    def test_18_api_image_hygiene(self, mock_gemini):
        jpeg_bytes = make_test_jpeg()
        resp = client.post(
            "/api/hygiene",
            files={"image": ("kitchen.jpg", jpeg_bytes, "image/jpeg")},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["media_type"], "image")
        self.assertIn("compliance_score", data)
        self.assertIn("coverage", data)
        self.assertIn("alerts", data)
        self.assertIn("findings", data)
        self.assertIsNone(data["frames_telemetry"])

    @patch("app._call_gemini_json", return_value=(mock_gemini_hygiene_response(gloves_ok=False), "gemini-3.8-flash"))
    def test_19_api_video_hygiene(self, mock_gemini):
        video_bytes = create_synthetic_mp4(num_frames=20, fps=10.0)
        resp = client.post(
            "/api/hygiene",
            files={"image": ("kitchen_inspection.mp4", video_bytes, "video/mp4")},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["media_type"], "video")
        self.assertIsNotNone(data["frames_telemetry"])
        self.assertGreater(len(data["observations"]), 0)
        self.assertTrue(any(a["indicator"] == "gloves_ppe" for a in data["alerts"]))

    def test_20_api_unsupported_mime(self):
        resp = client.post(
            "/api/hygiene",
            files={"image": ("doc.pdf", b"%PDF-1.4...", "application/pdf")},
        )
        self.assertEqual(resp.status_code, 415)

    @patch("app._call_gemini_json", side_effect=RuntimeError("Gemini quota exceeded"))
    def test_21_api_gemini_failure_fallback(self, mock_gemini):
        jpeg_bytes = make_test_jpeg()
        resp = client.post(
            "/api/hygiene",
            files={"image": ("kitchen.jpg", jpeg_bytes, "image/jpeg")},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["compliance_score"], 0)
        self.assertEqual(data["coverage"], 0.0)
        self.assertIn("limitations", data)

    @patch("app._call_gemini_json", return_value=({"status": "fresh", "label": "Fresh", "certainty": "High", "food_item": "Apple"}, "gemini-3.8-flash"))
    def test_22_regressions_predict_freshness(self, mock_gemini):
        # Predict regression
        resp_p = client.post(
            "/api/predict",
            files={"image": ("sample.jpg", make_test_jpeg(), "image/jpeg")},
        )
        self.assertEqual(resp_p.status_code, 200)

        # Freshness regression
        resp_f = client.post(
            "/api/freshness",
            files={"image": ("sample.jpg", make_test_jpeg(), "image/jpeg")},
        )
        self.assertEqual(resp_f.status_code, 200)
        self.assertIn("evidence_level", resp_f.json())


if __name__ == "__main__":
    unittest.main(verbosity=2)

#===========================================================================
# Section: test_activity_4_2.py
#===========================================================================

"""
FoodVerse AI — Smart Bridge Activity 4.2 Test Suite
Smart Kitchen Cooking Guidance and Recipe Generation Logic

Tests:
  01. build_recipe_prompt: produces complete contextual prompt including ingredients, diet, cuisine, and skill.
  02. build_recipe_prompt: includes visual ingredients context when present.
  03. normalize_recipe_response: normalizes full raw Gemini response into valid Activity 4.2 schema.
  04. normalize_recipe_response: safely handles empty, None, or partial Gemini dict with robust defaults.
  05. normalize_recipe_response: defaults food safety reminders and cooking tips when absent.
  06. build_ingredient_vision_prompt: returns structured schema requesting is_food and detected_ingredients.
  07. POST /api/cooking: generates structured recipe with HTTP 200 from valid text ingredients.
  08. POST /api/cooking: returns HTTP 400 when ingredients list is empty or whitespace-only.
  09. POST /api/cooking: gracefully handles Gemini failure with HTTP 502 and actionable error details.
  10. POST /api/cooking: respects skill_level, cooking_objective, and intended_dish parameters.
  11. POST /api/cooking: logs generated recipe into SQLite activity_logs.
  12. POST /api/cooking/detect-ingredients: returns HTTP 200 with detected ingredients on valid image.
  13. POST /api/cooking/detect-ingredients: returns HTTP 415 on unsupported media type (e.g. PDF/TXT).
  14. POST /api/cooking/detect-ingredients: returns HTTP 400 on 0-byte upload.
  15. POST /api/cooking/detect-ingredients: handles non-food images safely (is_food=False).
  16. Regression: POST /api/predict (2.1), /api/freshness (3.2), and /api/hygiene (4.1) remain operational.
"""

import io
import unittest
import warnings
from unittest.mock import patch, MagicMock

from PIL import Image

warnings.filterwarnings('ignore', message=r'.*starlette\.testclient.*')

from fastapi.testclient import TestClient

import app
import cooking_service

client = TestClient(app.app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_test_image(width: int = 150, height: int = 150, color: tuple = (100, 180, 80)) -> bytes:
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def mock_gemini_recipe_response() -> dict:
    return {
        "name": "Palak Paneer Bhurji",
        "emoji": "🧀",
        "description": "A fragrant, protein-packed scramble of paneer and fresh spinach tossed with cumin and green chillies.",
        "prep_time_mins": 10,
        "cook_time_mins": 15,
        "time": 25,
        "servings": 2,
        "diet": "vegetarian",
        "cuisine": "Indian",
        "skill_level": "Beginner",
        "calories": 280,
        "ingredients": [
            {"n": "Fresh Spinach", "q": "200g (washed and finely chopped)"},
            {"n": "Paneer", "q": "150g (crumbled)"},
            {"n": "Onion", "q": "1 medium (finely chopped)"},
            {"n": "Cooking Oil", "q": "1 tbsp"},
            {"n": "Cumin Seeds", "q": "1/2 tsp"}
        ],
        "steps": [
            "Wash spinach thoroughly under cold water; finely chop and set aside.",
            "Heat 1 tbsp cooking oil in a non-stick pan over medium heat; add cumin seeds until they sizzle (~30s).",
            "Add chopped onions; sauté until translucent and aromatic, about 3-4 minutes.",
            "Add chopped spinach; cook down until wilted and moisture evaporates, about 4 minutes.",
            "Gently fold in crumbled paneer and salt to taste; heat through for 2 minutes before serving."
        ],
        "cooking_tips": [
            "Do not overcook paneer as it can turn rubbery; fold it in at the very end.",
            "Squeeze excess water from washed spinach leaves before chopping."
        ],
        "substitutions": [
            "Firm tofu can be substituted for paneer for a 100% vegan variation."
        ],
        "food_safety_reminders": [
            "Wash hands thoroughly before handling fresh produce.",
            "Ensure paneer is stored below 4 °C until ready to use."
        ],
        "nutrition_tip": "Spinach provides bioavailable dietary iron and beta-carotene, while paneer contributes essential casein protein.",
        "assumptions": [
            "Assumed cooking oil and salt are available staples."
        ]
    }


def mock_gemini_vision_ingredients_response(is_food: bool = True) -> dict:
    if is_food:
        return {
            "is_food": True,
            "detected_ingredients": ["Spinach", "Tomatoes", "Garlic", "Paneer"],
            "observations": "Fresh bundle of leafy spinach with two red tomatoes and a block of white cottage cheese.",
            "confidence_note": "Ingredients clearly visible under good ambient lighting."
        }
    return {
        "is_food": False,
        "detected_ingredients": [],
        "observations": "Image displays kitchen cutlery and a cutting board without visible food items.",
        "confidence_note": "No edible items identified."
    }


# ---------------------------------------------------------------------------
# Unit tests: cooking_service
# ---------------------------------------------------------------------------

class TestCookingService(unittest.TestCase):

    def test_01_build_recipe_prompt_basic(self):
        prompt = cooking_service.build_recipe_prompt(
            ingredients=["Paneer", "Spinach", "Tomatoes"],
            diet="Vegetarian",
            servings=3,
            cuisine="North Indian",
            max_time_mins=25,
            skill_level="Beginner",
        )
        self.assertIn("Paneer, Spinach, Tomatoes", prompt)
        self.assertIn("Vegetarian", prompt)
        self.assertIn("North Indian", prompt)
        self.assertIn("Target Servings: 3", prompt)
        self.assertIn("food_safety_reminders", prompt)
        self.assertIn("cooking_tips", prompt)

    def test_02_build_recipe_prompt_with_vision(self):
        prompt = cooking_service.build_recipe_prompt(
            ingredients=["Spinach"],
            visual_identified_ingredients=["Spinach", "Garlic"],
        )
        self.assertIn("Ingredients Detected via Vision: Spinach, Garlic", prompt)

    def test_03_normalize_recipe_response_valid(self):
        raw = mock_gemini_recipe_response()
        norm = cooking_service.normalize_recipe_response(
            raw_data=raw,
            requested_servings=2,
            requested_diet="Vegetarian",
            cuisine="Indian",
            model_used="gemini-3.8-flash",
        )
        self.assertEqual(norm["name"], "Palak Paneer Bhurji")
        self.assertEqual(norm["prep_time_mins"], 10)
        self.assertEqual(norm["cook_time_mins"], 15)
        self.assertEqual(norm["time"], 25)
        self.assertEqual(norm["servings"], 2)
        self.assertEqual(len(norm["steps"]), 5)
        self.assertEqual(len(norm["cooking_tips"]), 2)
        self.assertEqual(len(norm["food_safety_reminders"]), 2)
        self.assertEqual(norm["engine"], "gemini-3.8-flash LLM")

    def test_04_normalize_recipe_response_empty_fallback(self):
        norm = cooking_service.normalize_recipe_response(
            raw_data=None,
            requested_servings=4,
            requested_diet="Vegan",
            cuisine="Mediterranean",
        )
        self.assertEqual(norm["name"], "Custom Kitchen Creation")
        self.assertEqual(norm["servings"], 4)
        self.assertGreater(len(norm["steps"]), 0)
        self.assertGreater(len(norm["ingredients"]), 0)
        self.assertGreater(len(norm["food_safety_reminders"]), 0)

    def test_05_normalize_recipe_response_default_tips_and_safety(self):
        # Omit tips and safety from raw input
        partial = {"name": "Quick Salad", "steps": ["Chop ingredients", "Toss"]}
        norm = cooking_service.normalize_recipe_response(raw_data=partial)
        self.assertIsInstance(norm["cooking_tips"], list)
        self.assertGreater(len(norm["cooking_tips"]), 0)
        self.assertIsInstance(norm["food_safety_reminders"], list)
        self.assertGreater(len(norm["food_safety_reminders"]), 0)

    def test_06_build_ingredient_vision_prompt(self):
        prompt = cooking_service.build_ingredient_vision_prompt()
        self.assertIn("is_food", prompt)
        self.assertIn("detected_ingredients", prompt)
        self.assertIn("confidence_note", prompt)


# ---------------------------------------------------------------------------
# Integration tests: POST /api/cooking via TestClient
# ---------------------------------------------------------------------------

class TestCookingAPIIntegration(unittest.TestCase):

    @patch("app._call_gemini_json", return_value=(mock_gemini_recipe_response(), "gemini-3.8-flash"))
    def test_07_post_cooking_success(self, mock_gemini):
        payload = {
            "ingredients": ["Spinach", "Paneer"],
            "diet": "Vegetarian",
            "servings": 2,
            "cuisine": "Indian",
            "max_time_mins": 30,
        }
        resp = client.post("/api/cooking", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["name"], "Palak Paneer Bhurji")
        self.assertIn("prep_time_mins", data)
        self.assertIn("cook_time_mins", data)
        self.assertIn("cooking_tips", data)
        self.assertIn("food_safety_reminders", data)
        self.assertIn("nutrition_tip", data)

    def test_08_post_cooking_empty_ingredients(self):
        resp = client.post("/api/cooking", json={"ingredients": []})
        self.assertEqual(resp.status_code, 400)

        resp2 = client.post("/api/cooking", json={"ingredients": ["  ", ""]})
        self.assertEqual(resp2.status_code, 400)

    @patch("app._call_gemini_json", side_effect=RuntimeError("API quota exhausted"))
    def test_09_post_cooking_gemini_failure(self, mock_gemini):
        payload = {"ingredients": ["Rice", "Lentils"]}
        resp = client.post("/api/cooking", json=payload)
        self.assertEqual(resp.status_code, 502)
        self.assertIn("Gemini recipe generation failed", resp.json()["detail"])

    @patch("app._call_gemini_json", return_value=(mock_gemini_recipe_response(), "gemini-3.8-flash"))
    def test_10_post_cooking_extended_context(self, mock_gemini):
        payload = {
            "ingredients": ["Paneer", "Peas"],
            "skill_level": "Intermediate",
            "cooking_objective": "High Protein Dinner",
            "intended_dish": "Matar Paneer Curry",
            "visual_identified_ingredients": ["Paneer", "Green Peas"],
        }
        resp = client.post("/api/cooking", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["visual_ingredients_detected"], ["Paneer", "Green Peas"])

    @patch("app._call_gemini_json", return_value=(mock_gemini_recipe_response(), "gemini-3.8-flash"))
    def test_11_post_cooking_logs_to_database(self, mock_gemini):
        payload = {"ingredients": ["Potato", "Cumin"]}
        resp = client.post("/api/cooking", json=payload)
        self.assertEqual(resp.status_code, 200)

        # Check DB log
        import database
        activities = database.get_recent_activities(limit=5)
        has_cook_log = any(a["module"] == "cooking" for a in activities)
        self.assertTrue(has_cook_log)

    @patch("app._call_gemini_json", return_value=(mock_gemini_vision_ingredients_response(is_food=True), "gemini-3.8-flash"))
    def test_12_detect_ingredients_image_success(self, mock_gemini):
        img_bytes = make_test_image()
        resp = client.post(
            "/api/cooking/detect-ingredients",
            files={"image": ("produce.jpg", img_bytes, "image/jpeg")},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["is_food"])
        self.assertIn("Spinach", data["detected_ingredients"])
        self.assertIn("observations", data)

    def test_13_detect_ingredients_unsupported_mime(self):
        resp = client.post(
            "/api/cooking/detect-ingredients",
            files={"image": ("list.txt", b"spinach, paneer", "text/plain")},
        )
        self.assertEqual(resp.status_code, 415)

    def test_14_detect_ingredients_empty_upload(self):
        resp = client.post(
            "/api/cooking/detect-ingredients",
            files={"image": ("empty.jpg", b"", "image/jpeg")},
        )
        self.assertEqual(resp.status_code, 400)

    @patch("app._call_gemini_json", return_value=(mock_gemini_vision_ingredients_response(is_food=False), "gemini-3.8-flash"))
    def test_15_detect_ingredients_non_food(self, mock_gemini):
        img_bytes = make_test_image()
        resp = client.post(
            "/api/cooking/detect-ingredients",
            files={"image": ("countertop.jpg", img_bytes, "image/jpeg")},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data["is_food"])
        self.assertEqual(len(data["detected_ingredients"]), 0)

    @patch("app._call_gemini_json", return_value=({"status": "fresh", "label": "Fresh", "certainty": "High", "food_item": "Apple"}, "gemini-3.8-flash"))
    def test_16_regressions_milestones_2_3_4(self, mock_gemini):
        # 2.1 Predict
        resp_p = client.post("/api/predict", files={"image": ("sample.jpg", make_test_image(), "image/jpeg")})
        self.assertEqual(resp_p.status_code, 200)

        # 3.2 Freshness
        resp_f = client.post("/api/freshness", files={"image": ("sample.jpg", make_test_image(), "image/jpeg")})
        self.assertEqual(resp_f.status_code, 200)

        # 4.1 Hygiene
        with patch("app._call_gemini_json", return_value=({
            "observations": [{"indicator": "surface_cleanliness", "status": "observed", "evidence": "clean"}],
            "frame_summary": "clean"
        }, "gemini-3.8-flash")):
            resp_h = client.post("/api/hygiene", files={"image": ("sample.jpg", make_test_image(), "image/jpeg")})
            self.assertEqual(resp_h.status_code, 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)


if __name__ == "__main__":
    unittest.main()
