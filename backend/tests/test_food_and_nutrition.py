"""
FoodVerse AI — Test Suite: Food Recognition & Nutrition Estimation
Consolidates test_activity_2_1.py and test_activity_2_2.py.
"""

"""
FoodVerse AI — Smart Bridge Activity 2.1 Verification Suite
Food Image Detection and Classification Test Suite

Tests:
1. test_opencv_preprocessing_valid_jpeg: Verifies JPEG decoding, RGB conversion, and telemetry.
2. test_opencv_preprocessing_valid_png: Verifies PNG decoding and RGB conversion.
3. test_opencv_preprocessing_valid_webp: Verifies WebP decoding and RGB conversion.
4. test_opencv_preprocessing_oversized_resize: Verifies aspect-ratio-preserving downscale.
5. test_corrupt_image_rejection: Verifies 400 rejection for random corrupt bytes.
6. test_empty_image_rejection: Verifies 400 rejection for 0-byte upload.
7. test_unsupported_format_rejection: Verifies 415 rejection for non-image MIME types.
8. test_oversized_upload_rejection: Verifies 413 rejection for files exceeding MAX_MB.
9. test_predict_mocked_food_classification: Verifies structured schema for food dish.
10. test_predict_mocked_non_food_classification: Verifies non-food detection and schema.
11. test_predict_real_smoke_test: Live smoke test against Gemini API (if key available).
"""

import io
import os
import unittest
import warnings
from unittest.mock import patch, MagicMock
import numpy as np
from PIL import Image

# Suppress StarletteDeprecationWarning issued by Starlette 1.8.0 when TestClient wraps httpx
warnings.filterwarnings('ignore', message=r'.*starlette\.testclient.*')

from fastapi.testclient import TestClient

import app
import database


def create_test_image_bytes(format='JPEG', size=(400, 300), color=(180, 120, 60)) -> bytes:
    """Creates in-memory image bytes in the specified format."""
    img = Image.new('RGB', size, color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


class TestActivity21FoodDetection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app.app)

    def test_01_opencv_preprocessing_valid_jpeg(self):
        """Verifies OpenCV correctly decodes JPEG, converts BGR->RGB, and outputs telemetry."""
        raw = create_test_image_bytes('JPEG', (500, 400), (200, 100, 50))
        pil_img, tele = app.preprocess_image_opencv(raw)
        self.assertIsInstance(pil_img, Image.Image)
        self.assertEqual(pil_img.size, (500, 400))
        self.assertEqual(tele['original_dimensions'], [500, 400])
        self.assertEqual(tele['processed_dimensions'], [500, 400])
        self.assertFalse(tele['resized'])
        self.assertEqual(tele['color_space'], 'RGB')
        self.assertIn('OpenCV', tele['engine'])

    def test_02_opencv_preprocessing_valid_png(self):
        """Verifies OpenCV correctly decodes PNG images."""
        raw = create_test_image_bytes('PNG', (300, 300), (50, 150, 250))
        pil_img, tele = app.preprocess_image_opencv(raw)
        self.assertIsInstance(pil_img, Image.Image)
        self.assertEqual(pil_img.size, (300, 300))
        self.assertEqual(tele['color_space'], 'RGB')

    def test_03_opencv_preprocessing_valid_webp(self):
        """Verifies OpenCV correctly decodes WebP images."""
        raw = create_test_image_bytes('WEBP', (250, 250), (100, 200, 100))
        pil_img, tele = app.preprocess_image_opencv(raw)
        self.assertIsInstance(pil_img, Image.Image)
        self.assertEqual(pil_img.size, (250, 250))
        self.assertEqual(tele['color_space'], 'RGB')

    def test_04_opencv_preprocessing_oversized_resize(self):
        """Verifies oversized images (>1600px) are downscaled while preserving aspect ratio."""
        raw = create_test_image_bytes('JPEG', (2400, 1800), (150, 75, 200))
        pil_img, tele = app.preprocess_image_opencv(raw)
        self.assertTrue(tele['resized'])
        self.assertEqual(tele['original_dimensions'], [2400, 1800])
        # Maximum dimension should now equal MAX_IMG_DIMENSION (1600)
        self.assertEqual(tele['processed_dimensions'][0], 1600)
        # 1800 * (1600/2400) = 1200
        self.assertEqual(tele['processed_dimensions'][1], 1200)
        self.assertEqual(pil_img.size, (1600, 1200))

    def test_05_corrupt_image_rejection(self):
        """Verifies corrupt bytes with image MIME type are rejected with 400 Bad Request."""
        corrupt_bytes = b"NOT_AN_IMAGE_RANDOM_CORRUPT_BYTES_1234567890"
        resp = self.client.post(
            '/api/predict',
            files={'image': ('corrupt.jpg', corrupt_bytes, 'image/jpeg')}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn('Corrupt, unreadable, or unsupported', resp.json().get('detail', ''))

    def test_06_empty_image_rejection(self):
        """Verifies empty (0-byte) image uploads are rejected with 400 Bad Request."""
        resp = self.client.post(
            '/api/predict',
            files={'image': ('empty.jpg', b'', 'image/jpeg')}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn('Empty image file', resp.json().get('detail', ''))

    def test_07_unsupported_format_rejection(self):
        """Verifies unsupported MIME types (e.g. application/pdf) are rejected with 415."""
        resp = self.client.post(
            '/api/predict',
            files={'image': ('document.pdf', b'%PDF-1.4 test', 'application/pdf')}
        )
        self.assertEqual(resp.status_code, 415)
        self.assertIn('Unsupported file format', resp.json().get('detail', ''))

    def test_08_oversized_upload_rejection(self):
        """Verifies uploads exceeding MAX_MB (10MB) are rejected with 413."""
        huge_bytes = b'0' * (11 * 1024 * 1024)  # 11 MB
        resp = self.client.post(
            '/api/predict',
            files={'image': ('huge.jpg', huge_bytes, 'image/jpeg')}
        )
        self.assertEqual(resp.status_code, 413)
        self.assertIn('Image too large', resp.json().get('detail', ''))

    def test_09_predict_mocked_food_classification(self):
        """Verifies successful food classification returns the full structured schema."""
        raw = create_test_image_bytes('JPEG', (400, 400), (220, 150, 80))
        mock_gemini_response = {
            "is_food": True,
            "predicted_class": "Chole Bhature",
            "description": "Fluffy deep-fried bhatura paired with rich spiced chickpea curry.",
            "confidence": "High",
            "confidence_score": 0.94,
            "confidence_note": "Distinct puffed bhatura texture and dark chickpea gravy visible",
            "food_items": ["Bhatura bread", "Chole chickpeas", "Pickled onion garnish"],
            "visual_observations": [
                "Golden-brown crisp surface on large inflated bread",
                "Dark amber spiced gravy with visible chickpeas",
                "Onion rings with lime wedge garnish on the side"
            ],
            "nutrition": {
                "serving": "1 plate (2 bhature + 200g chole)",
                "calories": 650,
                "protein": 18,
                "carbs": 82,
                "fat": 28,
                "fiber": 10,
                "tip": "High in protein and fiber from chickpeas; balance with a light dinner."
            }
        }

        with patch('app._call_gemini_json', return_value=(mock_gemini_response, 'gemini-3.5-flash-lite')):
            resp = self.client.post(
                '/api/predict',
                files={'image': ('chole.jpg', raw, 'image/jpeg')}
            )

        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        # Verify structured contract
        self.assertTrue(data['success'])
        self.assertTrue(data['is_food'])
        self.assertEqual(data['food_name'], 'Chole Bhature')
        self.assertEqual(data['predicted_class'], 'Chole Bhature')
        self.assertEqual(data['confidence'], 'High')
        self.assertGreaterEqual(data['confidence_score'], 0.5)
        self.assertEqual(data['certainty'], 'High')
        self.assertIn('Bhatura bread', data['food_items'])
        self.assertGreater(len(data['visual_observations']), 0)
        self.assertIn(data['nutrition']['calories'], [520, 650])
        self.assertIn('preprocessing_applied', data)
        self.assertEqual(data['preprocessing_applied']['color_space'], 'RGB')
        self.assertIn('OpenCV', data['preprocessing_applied']['engine'])

    def test_10_predict_mocked_non_food_classification(self):
        """Verifies non-food objects are properly recognized without hallucinating dishes."""
        raw = create_test_image_bytes('JPEG', (400, 400), (50, 50, 50))
        mock_non_food_response = {
            "is_food": False,
            "predicted_class": "Unrecognized Non-Food Object",
            "description": "Image shows an office desk with a laptop keyboard and monitor.",
            "confidence": "Low",
            "confidence_score": 0.12,
            "confidence_note": "Visual analysis detected electronic hardware rather than food",
            "food_items": [],
            "visual_observations": [
                "Rectangular plastic keyboard keys visible",
                "Absence of food textures, organic matter, or culinary garnishes"
            ],
            "nutrition": None
        }

        with patch('app._call_gemini_json', return_value=(mock_non_food_response, 'gemini-3.5-flash-lite')):
            resp = self.client.post(
                '/api/predict',
                files={'image': ('laptop.jpg', raw, 'image/jpeg')}
            )

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertFalse(data['is_food'])
        self.assertEqual(data['predicted_class'], 'Unrecognized Non-Food Object')
        self.assertEqual(data['confidence'], 'Low')
        self.assertIsNone(data['nutrition'])
        self.assertEqual(len(data['food_items']), 0)
        self.assertIn('preprocessing_applied', data)

    def test_11_health_endpoint_reports_opencv(self):
        """Verifies health endpoint reports OpenCV preprocessor status."""
        resp = self.client.get('/api/health')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('image_preprocessor', data)
        self.assertIn('OpenCV', data['image_preprocessor'])

#===========================================================================
# Section: test_activity_2_2.py
#===========================================================================

"""
FoodVerse AI — Smart Bridge Activity 2.2 Test Suite
Nutrition Estimation, Health Scoring, and Dietary Insights

Tests:
  1. Known food matched to documented reference profile (ICMR IFCT / USDA FDC).
  2. Correct portion-size scaling when serving weight is known.
  3. Unknown food fallback to sanitized AI visual estimation with uncertainty disclosures.
  4. Missing, malformed, negative, or non-finite nutrition values sanitization.
  5. Non-food classification suppressing nutrition output.
  6. Deterministic health scoring for identical inputs.
  7. Health scoring component sensitivity (protein, fiber, fat ratio, excess calories).
  8. Correct handling of insufficient data for scoring without fabricating zeroes.
  9. Practical dietary insights generation grounded in computed thresholds.
  10. Full /api/predict API contract verification with Activity 2.2 schema.
  11. Health endpoint reporting nutritional estimation capability.
"""

import io
import math
import unittest
import warnings
from unittest.mock import patch

# Suppress StarletteDeprecationWarning issued by Starlette 1.8.0 when TestClient wraps httpx
warnings.filterwarnings('ignore', message=r'.*starlette\.testclient.*')

from fastapi.testclient import TestClient
from PIL import Image

import app
import nutrition_service


def create_dummy_jpeg(width=300, height=300, color=(180, 80, 40)) -> bytes:
    img = Image.new('RGB', (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return buf.getvalue()


class TestActivity22NutritionAndHealthScore(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app.app)

    # ── 1. Known Food Reference Profile Matching ──────────────────────────────
    def test_01_known_food_matches_reference_profile(self):
        """Verifies recognized food matches documented ICMR-NIN IFCT reference tables."""
        res = nutrition_service.estimate_nutrition_and_score(
            food_name="Chole Bhature",
            food_items=["Bhatura bread", "Chole curry"],
            gemini_raw_nutrition={"serving": "1 plate"},
            is_food=True
        )

        self.assertIsNotNone(res)
        self.assertEqual(res["status"], "available")
        self.assertEqual(res["calories"], 520)
        self.assertEqual(res["protein"], 14.5)
        self.assertEqual(res["carbs"], 68.0)
        self.assertEqual(res["fat"], 22.0)
        self.assertEqual(res["fiber"], 8.5)
        self.assertEqual(res["estimation_method"], "reference_standard")
        self.assertIn("ICMR-NIN", res["data_source"])
        self.assertIn("IFCT 2017", res["data_source"])
        self.assertIsNotNone(res["health_score"])
        self.assertGreaterEqual(res["health_score"], 0)
        self.assertLessEqual(res["health_score"], 100)

    # ── 2. Portion Scaling with Known Weight ─────────────────────────────────
    def test_02_portion_scaling_with_known_weight(self):
        """Verifies linear scaling when explicit serving gram weight is detected."""
        # Palak Paneer baseline: 230g, 290 kcal, 15.5g protein
        # Scaled to 460g (~2.0x portion)
        res = nutrition_service.estimate_nutrition_and_score(
            food_name="Palak Paneer",
            food_items=["Spinach gravy", "Paneer cubes"],
            gemini_raw_nutrition={"serving": "large bowl (approx 460g)"},
            is_food=True
        )

        self.assertEqual(res["estimation_method"], "reference_portion_scaled")
        self.assertIn("Portion scaled to 460g", res["data_source"])
        self.assertEqual(res["calories"], 580)  # 290 * 2.0
        self.assertAlmostEqual(res["protein"], 31.0, places=1)  # 15.5 * 2.0
        self.assertAlmostEqual(res["fiber"], 11.6, places=1)   # 5.8 * 2.0

    # ── 3. Unknown Food AI Estimation Fallback ────────────────────────────────
    def test_03_unknown_food_ai_estimation_fallback(self):
        """Verifies unlisted custom or mixed dish falls back to sanitized AI visual estimation."""
        raw_ai = {
            "calories": 410,
            "protein": 12.0,
            "carbs": 55.0,
            "fat": 15.0,
            "fiber": 6.0,
            "serving": "1 bowl (approx 320g)",
            "tip": "Balanced custom bowl"
        }
        res = nutrition_service.estimate_nutrition_and_score(
            food_name="Moroccan Spiced Couscous with Vegetables",
            food_items=["Couscous", "Chickpeas", "Zucchini"],
            gemini_raw_nutrition=raw_ai,
            is_food=True
        )

        self.assertEqual(res["status"], "available")
        self.assertEqual(res["estimation_method"], "ai_visual_estimation")
        self.assertIn("Gemini Multimodal AI", res["data_source"])
        self.assertEqual(res["calories"], 410)
        self.assertIn("Provisional AI visual estimation", res["uncertainty_note"])

    # ── 4. Missing, Malformed, Negative & Non-Finite Value Sanitization ──────
    def test_04_missing_negative_non_finite_sanitization(self):
        """Verifies negative numbers, NaNs, and infinities are safely rejected or sanitized."""
        # Scenario A: Negative and NaN values
        raw_bad = {
            "calories": -500,
            "protein": float("nan"),
            "carbs": float("inf"),
            "fat": "not_a_number"
        }
        res = nutrition_service.estimate_nutrition_and_score(
            food_name="Exotic Mystery Stew",
            food_items=[],
            gemini_raw_nutrition=raw_bad,
            is_food=True
        )
        self.assertEqual(res["status"], "insufficient_data")
        self.assertIsNone(res["calories"])
        self.assertIsNone(res["health_score"])
        self.assertEqual(res["health_score_label"], "Insufficient Data")

        # Scenario B: Single macro provided with positive calories
        sanitized, status = nutrition_service.validate_and_balance_nutrition({
            "calories": 200,
            "protein": 10,
            "carbs": 25,
            "fat": None
        })
        self.assertEqual(status, "available")
        self.assertEqual(sanitized["fat"], 0.0)
        self.assertEqual(sanitized["protein"], 10.0)

    # ── 5. Non-Food Classification Suppresses Nutrition ──────────────────────
    def test_05_non_food_suppresses_nutrition(self):
        """Verifies is_food=False suppresses nutrition output completely."""
        res = nutrition_service.estimate_nutrition_and_score(
            food_name="Laptop Computer",
            food_items=[],
            gemini_raw_nutrition={"calories": 500},
            is_food=False
        )
        self.assertIsNone(res)

    # ── 6. Deterministic Health Scoring ──────────────────────────────────────
    def test_06_deterministic_health_scoring(self):
        """Verifies health score produces the exact same integer and breakdown for identical inputs."""
        nut_input = {
            "calories": 350,
            "protein": 16.0,
            "carbs": 45.0,
            "fat": 10.0,
            "fiber": 7.5
        }
        score1, label1, bd1 = nutrition_service.compute_health_score(nut_input)
        score2, label2, bd2 = nutrition_service.compute_health_score(nut_input)

        self.assertEqual(score1, score2)
        self.assertEqual(label1, label2)
        self.assertEqual(bd1, bd2)
        self.assertIsInstance(score1, int)
        self.assertGreaterEqual(score1, 10)
        self.assertLessEqual(score1, 100)

    # ── 7. Health Score Component Sensitivity ────────────────────────────────
    def test_07_health_score_components_and_penalties(self):
        """Verifies health score responds logically to protein, fiber, and high lipid concentration."""
        # Balanced dish: high protein (18g), high fiber (8g), moderate fat (10g)
        balanced = {
            "calories": 380,
            "protein": 18.0,
            "carbs": 50.0,
            "fat": 10.0,
            "fiber": 8.0
        }
        score_bal, label_bal, bd_bal = nutrition_service.compute_health_score(balanced)

        # Deep fried indulgent dish: low protein (3g), low fiber (1g), high fat (35g)
        fried = {
            "calories": 550,
            "protein": 3.0,
            "carbs": 45.0,
            "fat": 38.0,
            "fiber": 1.0
        }
        score_fried, label_fried, bd_fried = nutrition_service.compute_health_score(fried)

        self.assertGreater(score_bal, score_fried)
        self.assertIn("High dietary fiber", " ".join(bd_bal))
        self.assertIn("High protein content", " ".join(bd_bal))
        self.assertIn("Very high lipid concentration", " ".join(bd_fried))

    # ── 8. Insufficient Data for Scoring ─────────────────────────────────────
    def test_08_insufficient_data_handling(self):
        """Verifies insufficient data is reported honestly without fabricating scores."""
        score, label, breakdown = nutrition_service.compute_health_score({})
        self.assertIsNone(score)
        self.assertEqual(label, "Insufficient Data")

        score_zero_cals, _, _ = nutrition_service.compute_health_score({
            "calories": 0, "protein": 0, "carbs": 0, "fat": 0
        })
        self.assertIsNone(score_zero_cals)

    # ── 9. Practical Dietary Insights Generation ─────────────────────────────
    def test_09_dietary_insights_generation(self):
        """Verifies insights generate actionable suggestions without medical diagnosis."""
        # Low protein, low fiber, high calorie meal
        nut = {
            "calories": 720,
            "protein": 5.0,
            "carbs": 95.0,
            "fat": 32.0,
            "fiber": 1.5
        }
        insights = nutrition_service.generate_dietary_insights(nut)
        insights_str = " ".join(insights)

        self.assertIn("Portion Awareness", insights_str)
        self.assertIn("Protein Pairing Opportunity", insights_str)
        self.assertIn("Fiber Boost Suggestion", insights_str)

    # ── 10. /api/predict Full API Integration ────────────────────────────────
    def test_10_api_predict_integration_with_activity_2_2(self):
        """Verifies /api/predict returns full Activity 2.2 schema with health score and data source."""
        raw_img = create_dummy_jpeg(300, 300, (150, 90, 40))
        mock_gemini = {
            "is_food": True,
            "predicted_class": "Masala Dosa",
            "description": "Crisp fermented rice-lentil crepe with spiced potato filling.",
            "confidence": "High",
            "confidence_score": 0.96,
            "confidence_note": "Crisp golden crepe texture and visible coconut chutney.",
            "food_items": ["Dosa crepe", "Spiced potato masala", "Coconut chutney"],
            "visual_observations": [
                "Golden brown crisp exterior",
                "Folded triangular presentation",
                "Sides of sambar and chutney in stainless steel bowls"
            ],
            "nutrition": {
                "serving": "1 medium dosa (~200g)",
                "calories": 350,
                "protein": 7,
                "carbs": 52,
                "fat": 13,
                "fiber": 4,
                "tip": "Enjoy with vegetable sambar for added protein and fiber."
            }
        }

        with patch('app._call_gemini_json', return_value=(mock_gemini, 'gemini-3.5-flash-lite')):
            resp = self.client.post(
                '/api/predict',
                files={'image': ('dosa.jpg', raw_img, 'image/jpeg')}
            )

        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertTrue(data['success'])
        self.assertTrue(data['is_food'])
        self.assertEqual(data['food_name'], 'Masala Dosa')

        # Activity 2.2 Nutrition & Health Scoring Contract
        nut = data['nutrition']
        self.assertIsNotNone(nut)
        self.assertEqual(nut['status'], 'available')
        self.assertEqual(nut['calories'], 350)
        self.assertEqual(nut['protein'], 6.8)  # From ICMR-NIN IFCT 2017 reference
        self.assertEqual(nut['carbs'], 52.0)
        self.assertEqual(nut['fat'], 13.0)
        self.assertEqual(nut['fiber'], 4.2)
        self.assertIn('ICMR-NIN', nut['data_source'])
        self.assertEqual(nut['estimation_method'], 'reference_standard')
        self.assertIsInstance(nut['health_score'], int)
        self.assertGreaterEqual(nut['health_score'], 60)
        self.assertIn('health_score_label', nut)
        self.assertIsInstance(nut['health_score_breakdown'], list)
        self.assertIsInstance(nut['insights'], list)
        self.assertIn('uncertainty_note', nut)

    # ── 11. Health Endpoint Reports Nutrition Estimation ──────────────────────
    def test_11_health_endpoint_reports_activity_2_2(self):
        """Verifies health check lists Activity 2.2 nutrition estimation pipeline."""
        resp = self.client.get('/api/health')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('nutrition_estimation', data)
        self.assertIn('ICMR-NIN IFCT 2017', data['nutrition_estimation'])

    # ── 12. Palak Paneer Exact Mathematics Verification ──────────────────────
    def test_12_palak_paneer_exact_mathematics(self):
        """
        Explicitly verifies the Palak Paneer mathematical scoring consistency:
          Base: 60.0
          Protein (15.5g >= 15.0): +15.0
          Fiber (5.8g >= 4.0): +10.0
          Fat %: (20.0 * 9 / 290) = 62.1% (> 60%): -15.0
          Total: 60 + 15 + 10 - 15 = 70 (Balanced Meal).
          Confirms reported score agrees with the sum of all components.
        """
        res = nutrition_service.estimate_nutrition_and_score(
            food_name="Palak Paneer",
            food_items=["Spinach", "Paneer"],
            gemini_raw_nutrition={"serving": "1 bowl (~230g spinach gravy with paneer)"},
            is_food=True
        )
        self.assertEqual(res["health_score"], 70)
        self.assertEqual(res["health_score_label"], "Balanced Meal")
        bd_text = " ".join(res["health_score_breakdown"])
        self.assertIn("+15 pts: High protein content", bd_text)
        self.assertIn("+10 pts: Good dietary fiber content", bd_text)
        self.assertIn("-15 pts: Very high lipid concentration", bd_text)

    # ── 13. Serving Weight Extraction & Edge Cases ────────────────────────────
    def test_13_serving_weight_edge_cases(self):
        """
        Verifies serving weight parser avoids mistaking sub-ingredient weights in
        compound strings (e.g. '2 bhature + 200g chole') for total plate weight,
        and gracefully handles missing or extreme weight values.
        """
        # Compound string without explicit total marker should NOT scale dish by 200g
        w_compound = nutrition_service.parse_serving_weight_g("1 plate (2 bhature + 200g chole)")
        self.assertIsNone(w_compound)

        # Compound string with explicit total/approx marker should scale
        w_explicit = nutrition_service.parse_serving_weight_g("1 plate (2 bhature + chole, approx 420g)")
        self.assertEqual(w_explicit, 420.0)

        # Standalone simple portion
        w_simple = nutrition_service.parse_serving_weight_g("approx 350g")
        self.assertEqual(w_simple, 350.0)

        # Ambiguous descriptive serving without grams
        w_ambiguous = nutrition_service.parse_serving_weight_g("1 medium bowl")
        self.assertIsNone(w_ambiguous)

        # Extreme / implausible single-serving weight (>1500g or <30g)
        w_too_large = nutrition_service.parse_serving_weight_g("10000g feast")
        self.assertIsNone(w_too_large)
        w_too_small = nutrition_service.parse_serving_weight_g("2g pinch")
        self.assertIsNone(w_too_small)


if __name__ == "__main__":
    unittest.main()
