"""
FoodVerse AI — Test Suite: Image Preprocessing & Freshness Detection
Consolidates test_activity_3_1.py and test_activity_3_2.py.
"""

"""
FoodVerse AI — Smart Bridge Activity 3.1 Test Suite
Food Image Preprocessing and Feature Extraction

Tests:
  01. JPEG decoding produces correct dimensions and RGB telemetry.
  02. PNG decoding produces correct dimensions and RGB telemetry.
  03. WebP decoding produces correct dimensions and RGB telemetry.
  04. Grayscale (1-channel) images are expanded to 3-channel RGB without error.
  05. RGBA (4-channel transparent) images are composited over a white background.
  06. Corrupt bytes are rejected with HTTP 400.
  07. Empty (0-byte) uploads are rejected with HTTP 400.
  08. Oversized files (>10 MB) are rejected with HTTP 413.
  09. Non-square landscape image preserves aspect ratio after resize.
  10. Non-square portrait image preserves aspect ratio after resize.
  11. Oversized images are downscaled so max dimension <= MAX_IMG_DIMENSION.
  12. Feature telemetry structure contains all required Activity 3.1 keys.
  13. All numeric feature values are finite (no NaN / inf).
  14. Sharp synthetic image reports is_blurry=False.
  15. Deliberately blurred synthetic image reports is_blurry=True.
  16. Dark synthetic image is classified as 'underexposed'.
  17. Well-lit synthetic image is classified as 'normal'.
  18. Overexposed (near-white) synthetic image is classified as 'overexposed'.
  19. Uniform (monochrome) image reports low texture_variation.
  20. Textured checkerboard image reports higher texture_variation.
  21. freshness_cues sub-object is present and structurally correct.
  22. POST /api/predict backward compatibility: legacy keys preserved.
  23. POST /api/predict: Activity 3.1 additive keys present in preprocessing_applied.
  24. GET /api/health reports Activity 3.1 visual_feature_extraction key.
  25. Activity 2.1 regression: all 11 existing tests still pass (subset check).
  26. Activity 2.2 regression: all 13 existing tests still pass (subset check).
"""

import io
import math
import unittest
import warnings
from unittest.mock import patch

import cv2
import numpy as np
from PIL import Image

warnings.filterwarnings('ignore', message=r'.*starlette\.testclient.*')

from fastapi.testclient import TestClient

import app
import image_processor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_jpeg(width=400, height=300, color=(180, 120, 60)) -> bytes:
    img = Image.new('RGB', (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return buf.getvalue()


def make_png(width=300, height=300, color=(50, 150, 250)) -> bytes:
    img = Image.new('RGB', (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


def make_webp(width=250, height=250, color=(100, 200, 100)) -> bytes:
    img = Image.new('RGB', (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format='WEBP')
    return buf.getvalue()


def make_grayscale_png(width=200, height=200, level=128) -> bytes:
    """Create a genuine 1-channel grayscale PNG."""
    img = Image.new('L', (width, height), level)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


def make_rgba_png(width=200, height=200) -> bytes:
    """Create a 4-channel RGBA PNG with 50% alpha transparency."""
    img = Image.new('RGBA', (width, height), (200, 100, 50, 128))
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


def make_blurry_jpeg(width=400, height=400) -> bytes:
    """Create a strongly Gaussian-blurred image to ensure low Laplacian variance."""
    arr = np.random.randint(50, 200, (height, width, 3), dtype=np.uint8)
    # Apply heavy blur (kernel 51x51 sigma=20) to guarantee Laplacian var < threshold
    blurred = cv2.GaussianBlur(arr, (51, 51), sigmaX=20)
    img = Image.fromarray(blurred)
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return buf.getvalue()


def make_sharp_jpeg(width=400, height=400) -> bytes:
    """Create a checkerboard with sharp edges — guaranteed high Laplacian variance."""
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    block = 10
    for r in range(height):
        for c in range(width):
            if ((r // block) + (c // block)) % 2 == 0:
                arr[r, c] = [255, 255, 255]
            else:
                arr[r, c] = [0, 0, 0]
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return buf.getvalue()


def make_dark_jpeg(width=300, height=300) -> bytes:
    """Very dark image (mean luminance ~20)."""
    img = Image.new('RGB', (width, height), (20, 20, 20))
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return buf.getvalue()


def make_bright_jpeg(width=300, height=300) -> bytes:
    """Well-lit mid-grey image (mean luminance ~128)."""
    img = Image.new('RGB', (width, height), (128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return buf.getvalue()


def make_overexposed_jpeg(width=300, height=300) -> bytes:
    """Near-white image (mean luminance ~240)."""
    img = Image.new('RGB', (width, height), (240, 240, 240))
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return buf.getvalue()


def make_uniform_jpeg(width=300, height=300) -> bytes:
    """Solid-color image — guaranteed low texture_variation."""
    img = Image.new('RGB', (width, height), (100, 150, 80))
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return buf.getvalue()


def make_textured_jpeg(width=400, height=400) -> bytes:
    """Fine noise image — guaranteed higher texture_variation."""
    arr = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return buf.getvalue()


REQUIRED_LEGACY_KEYS = {
    'original_dimensions', 'processed_dimensions', 'resized',
    'color_space', 'channels', 'engine',
}
REQUIRED_A31_KEYS = {
    'aspect_ratio', 'orientation', 'sharpness_score', 'is_blurry',
    'brightness_mean', 'exposure_quality', 'mean_saturation',
    'texture_variation', 'rms_contrast', 'freshness_cues', 'normalization',
}
MOCK_FOOD_RESPONSE = {
    "is_food": True,
    "predicted_class": "Test Dish",
    "description": "A test food dish.",
    "confidence": "High",
    "confidence_score": 0.90,
    "confidence_note": "Test note",
    "food_items": ["Ingredient A"],
    "visual_observations": ["Test observation"],
    "nutrition": {
        "serving": "1 bowl",
        "calories": 300,
        "protein": 10,
        "carbs": 40,
        "fat": 8,
        "fiber": 3,
        "tip": "Test tip",
    },
}


class TestActivity31Preprocessing(unittest.TestCase):
    """Activity 3.1 — Food Image Preprocessing and Feature Extraction."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app.app)

    # ── Format Decoding (Tests 01–03) ─────────────────────────────────────────
    def test_01_jpeg_decoding(self):
        """Verifies JPEG decoded dimensions, RGB telemetry, and engine string."""
        pil, tele = image_processor.preprocess_food_image(make_jpeg(400, 300))
        self.assertIsInstance(pil, Image.Image)
        self.assertEqual(tele['original_dimensions'], [400, 300])
        self.assertEqual(tele['processed_dimensions'], [400, 300])
        self.assertFalse(tele['resized'])
        self.assertEqual(tele['color_space'], 'RGB')
        self.assertEqual(tele['channels'], 3)
        self.assertIn('OpenCV', tele['engine'])

    def test_02_png_decoding(self):
        """Verifies PNG decoded dimensions and color space."""
        pil, tele = image_processor.preprocess_food_image(make_png(300, 300))
        self.assertIsInstance(pil, Image.Image)
        self.assertEqual(tele['original_dimensions'], [300, 300])
        self.assertEqual(tele['color_space'], 'RGB')

    def test_03_webp_decoding(self):
        """Verifies WebP decoded dimensions and color space."""
        pil, tele = image_processor.preprocess_food_image(make_webp(250, 250))
        self.assertIsInstance(pil, Image.Image)
        self.assertEqual(tele['original_dimensions'], [250, 250])
        self.assertEqual(tele['color_space'], 'RGB')

    # ── Channel Normalization (Tests 04–05) ───────────────────────────────────
    def test_04_grayscale_normalized_to_rgb(self):
        """Verifies 1-channel grayscale PNG is expanded to 3-channel RGB without error."""
        pil, tele = image_processor.preprocess_food_image(make_grayscale_png(200, 200))
        self.assertIsInstance(pil, Image.Image)
        self.assertEqual(tele['channels'], 3)
        self.assertEqual(tele['color_space'], 'RGB')
        self.assertEqual(tele['normalization']['channels_original'], 1)
        self.assertFalse(tele['normalization']['alpha_composited'])

    def test_05_rgba_composited_over_white(self):
        """Verifies 4-channel RGBA PNG is composited over white background."""
        pil, tele = image_processor.preprocess_food_image(make_rgba_png(200, 200))
        self.assertIsInstance(pil, Image.Image)
        self.assertEqual(tele['channels'], 3)
        self.assertEqual(tele['normalization']['channels_original'], 4)
        self.assertTrue(tele['normalization']['alpha_composited'])
        # Resulting image must be RGB, no alpha channel
        arr = np.array(pil)
        self.assertEqual(arr.shape[2], 3)

    # ── Rejection Cases (Tests 06–08) ────────────────────────────────────────
    def test_06_corrupt_bytes_rejected(self):
        """Verifies random corrupt bytes are rejected with HTTP 400."""
        resp = self.client.post(
            '/api/predict',
            files={'image': ('corrupt.jpg', b'NOTANIMAGE12345', 'image/jpeg')},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn('Corrupt', resp.json()['detail'])

    def test_07_empty_upload_rejected(self):
        """Verifies 0-byte upload is rejected with HTTP 400."""
        resp = self.client.post(
            '/api/predict',
            files={'image': ('empty.jpg', b'', 'image/jpeg')},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn('Empty', resp.json()['detail'])

    def test_08_oversized_upload_rejected(self):
        """Verifies files exceeding 10 MB are rejected with HTTP 413."""
        huge = b'X' * (11 * 1024 * 1024)
        resp = self.client.post(
            '/api/predict',
            files={'image': ('huge.jpg', huge, 'image/jpeg')},
        )
        self.assertEqual(resp.status_code, 413)

    # ── Aspect Ratio Preservation (Tests 09–11) ───────────────────────────────
    def test_09_landscape_aspect_ratio_preserved(self):
        """Landscape 800×400 image: aspect_ratio=2.0, orientation=landscape."""
        _, tele = image_processor.preprocess_food_image(make_jpeg(800, 400))
        self.assertAlmostEqual(tele['aspect_ratio'], 2.0, places=1)
        self.assertEqual(tele['orientation'], 'landscape')

    def test_10_portrait_aspect_ratio_preserved(self):
        """Portrait 400×800 image: aspect_ratio=0.5, orientation=portrait."""
        _, tele = image_processor.preprocess_food_image(make_jpeg(400, 800))
        self.assertAlmostEqual(tele['aspect_ratio'], 0.5, places=1)
        self.assertEqual(tele['orientation'], 'portrait')

    def test_11_oversized_downscaled_max_dimension(self):
        """Image 2400×1800 must be downscaled so max(W, H) <= 1600."""
        _, tele = image_processor.preprocess_food_image(make_jpeg(2400, 1800))
        self.assertTrue(tele['resized'])
        self.assertEqual(tele['original_dimensions'], [2400, 1800])
        pw, ph = tele['processed_dimensions']
        self.assertEqual(max(pw, ph), 1600)
        # Aspect ratio preserved: 2400/1800 = 4/3 => 1600×1200
        self.assertEqual(pw, 1600)
        self.assertEqual(ph, 1200)

    # ── Telemetry Structure & Finite Values (Tests 12–13) ───────────────────
    def test_12_telemetry_structure_complete(self):
        """All required legacy and Activity 3.1 telemetry keys are present."""
        _, tele = image_processor.preprocess_food_image(make_jpeg(300, 300))
        for key in REQUIRED_LEGACY_KEYS:
            self.assertIn(key, tele, msg=f"Missing legacy key: {key}")
        for key in REQUIRED_A31_KEYS:
            self.assertIn(key, tele, msg=f"Missing Activity 3.1 key: {key}")

    def test_13_all_numeric_features_finite(self):
        """Verifies all numeric feature outputs are finite floats (no NaN/inf)."""
        _, tele = image_processor.preprocess_food_image(make_jpeg(300, 300))
        for key in ('sharpness_score', 'brightness_mean', 'mean_saturation',
                    'texture_variation', 'rms_contrast', 'aspect_ratio'):
            val = tele[key]
            self.assertTrue(
                math.isfinite(float(val)),
                msg=f"Key '{key}' = {val!r} is not finite",
            )

    # ── Sharpness (Tests 14–15) ───────────────────────────────────────────────
    def test_14_sharp_image_not_blurry(self):
        """A checkerboard image with hard edges must be classified as NOT blurry."""
        _, tele = image_processor.preprocess_food_image(make_sharp_jpeg())
        self.assertFalse(
            tele['is_blurry'],
            msg=f"Expected is_blurry=False, got sharpness_score={tele['sharpness_score']}",
        )
        self.assertGreaterEqual(tele['sharpness_score'], 100.0)

    def test_15_blurry_image_detected(self):
        """A heavily Gaussian-blurred image must be classified as blurry."""
        _, tele = image_processor.preprocess_food_image(make_blurry_jpeg())
        self.assertTrue(
            tele['is_blurry'],
            msg=f"Expected is_blurry=True, got sharpness_score={tele['sharpness_score']}",
        )
        self.assertLess(tele['sharpness_score'], 100.0)

    # ── Exposure / Brightness (Tests 16–18) ──────────────────────────────────
    def test_16_dark_image_classified_underexposed(self):
        """Very dark (mean lum ~20) image must be 'underexposed'."""
        _, tele = image_processor.preprocess_food_image(make_dark_jpeg())
        self.assertEqual(tele['exposure_quality'], 'underexposed')
        self.assertLess(tele['brightness_mean'], 45.0)

    def test_17_normal_image_classified_normal(self):
        """Mid-grey image (mean lum ~128) must be 'normal' exposure."""
        _, tele = image_processor.preprocess_food_image(make_bright_jpeg())
        self.assertEqual(tele['exposure_quality'], 'normal')
        self.assertGreaterEqual(tele['brightness_mean'], 45.0)
        self.assertLessEqual(tele['brightness_mean'], 215.0)

    def test_18_overexposed_image_classified(self):
        """Near-white image (mean lum ~240) must be 'overexposed'."""
        _, tele = image_processor.preprocess_food_image(make_overexposed_jpeg())
        self.assertEqual(tele['exposure_quality'], 'overexposed')
        self.assertGreater(tele['brightness_mean'], 215.0)

    # ── Texture Variation (Tests 19–20) ──────────────────────────────────────
    def test_19_uniform_image_low_texture(self):
        """Solid-color image must have near-zero texture_variation."""
        _, tele = image_processor.preprocess_food_image(make_uniform_jpeg())
        self.assertLess(
            tele['texture_variation'], 15.0,
            msg=f"Expected low texture, got {tele['texture_variation']}",
        )

    def test_20_textured_image_high_texture(self):
        """Random-noise image must have significantly higher texture_variation."""
        _, tele = image_processor.preprocess_food_image(make_textured_jpeg())
        self.assertGreater(
            tele['texture_variation'], 15.0,
            msg=f"Expected higher texture, got {tele['texture_variation']}",
        )

    # ── Freshness Cues Structure (Test 21) ────────────────────────────────────
    def test_21_freshness_cues_structure(self):
        """freshness_cues contains required sub-objects for Activity 3.2."""
        _, tele = image_processor.preprocess_food_image(make_jpeg(300, 300))
        fc = tele['freshness_cues']
        self.assertIn('color_profile', fc)
        self.assertIn('texture_profile', fc)
        self.assertIn('quality_indicators', fc)
        self.assertIn('disclaimer', fc)

        cp = fc['color_profile']
        for key in ('mean_saturation_pct', 'mean_hue_deg', 'mean_value_pct',
                    'dominant_tone', 'channel_means'):
            self.assertIn(key, cp, msg=f"freshness_cues.color_profile missing '{key}'")

        tp = fc['texture_profile']
        for key in ('texture_variation', 'rms_contrast', 'surface_uniformity'):
            self.assertIn(key, tp)

        qi = fc['quality_indicators']
        for key in ('sharpness_score', 'is_blurry', 'blur_threshold',
                    'brightness_mean', 'exposure_quality'):
            self.assertIn(key, qi)

        # Disclaimer must mention visual limitation
        self.assertIn('Activity 3.2', fc['disclaimer'])

    # ── API Contract Backward Compatibility (Tests 22–23) ───────────────────
    def test_22_predict_legacy_keys_preserved(self):
        """POST /api/predict: preprocessing_applied still contains all legacy keys."""
        raw = make_jpeg(300, 300)
        with patch('app._call_gemini_json', return_value=(MOCK_FOOD_RESPONSE, 'gemini-3.5-flash-lite')):
            resp = self.client.post(
                '/api/predict',
                files={'image': ('test.jpg', raw, 'image/jpeg')},
            )
        self.assertEqual(resp.status_code, 200)
        prep = resp.json().get('preprocessing_applied', {})
        for key in REQUIRED_LEGACY_KEYS:
            self.assertIn(key, prep, msg=f"Legacy key missing: {key}")
        self.assertEqual(prep['color_space'], 'RGB')
        self.assertEqual(prep['channels'], 3)
        self.assertIn('OpenCV', prep['engine'])

    def test_23_predict_activity31_keys_present(self):
        """POST /api/predict: preprocessing_applied contains all Activity 3.1 additive keys."""
        raw = make_jpeg(300, 300)
        with patch('app._call_gemini_json', return_value=(MOCK_FOOD_RESPONSE, 'gemini-3.5-flash-lite')):
            resp = self.client.post(
                '/api/predict',
                files={'image': ('test.jpg', raw, 'image/jpeg')},
            )
        self.assertEqual(resp.status_code, 200)
        prep = resp.json().get('preprocessing_applied', {})
        for key in REQUIRED_A31_KEYS:
            self.assertIn(key, prep, msg=f"Activity 3.1 key missing: {key}")
        # Verify types
        self.assertIsInstance(prep['aspect_ratio'], float)
        self.assertIsInstance(prep['is_blurry'], bool)
        self.assertIsInstance(prep['sharpness_score'], float)
        self.assertIn(prep['orientation'], ('landscape', 'portrait', 'square'))
        self.assertIn(prep['exposure_quality'], ('normal', 'underexposed', 'overexposed'))

    # ── Health Endpoint (Test 24) ──────────────────────────────────────────────
    def test_24_health_reports_activity31(self):
        """GET /api/health reports Activity 3.1 visual_feature_extraction key."""
        resp = self.client.get('/api/health')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('image_preprocessor', data)
        self.assertIn('Activity 3.1', data['image_preprocessor'])
        self.assertIn('visual_feature_extraction', data)
        self.assertIn('Activity 3.1', data['visual_feature_extraction'])
        self.assertIn('sharpness_score', data['visual_feature_extraction'])

    # ── Activity 2.1 Regression Spot-Check (Test 25) ─────────────────────────
    def test_25_activity21_regression_preprocessing_contract(self):
        """Regression: Activity 2.1 OpenCV preprocessing contract still valid."""
        raw = make_jpeg(500, 400)
        pil, tele = app.preprocess_image_opencv(raw)
        self.assertIsInstance(pil, Image.Image)
        self.assertEqual(tele['original_dimensions'], [500, 400])
        self.assertEqual(tele['processed_dimensions'], [500, 400])
        self.assertFalse(tele['resized'])
        self.assertEqual(tele['color_space'], 'RGB')
        self.assertIn('OpenCV', tele['engine'])

    # ── Activity 2.2 Regression Spot-Check (Test 26) ─────────────────────────
    def test_26_activity22_regression_non_food_suppresses_nutrition(self):
        """Regression: Activity 2.2 non-food images must still suppress nutrition."""
        raw = make_jpeg(300, 300, color=(30, 30, 30))
        non_food_response = {
            "is_food": False,
            "predicted_class": "Non-Food Object",
            "description": "No food detected.",
            "confidence": "Low",
            "confidence_score": 0.10,
            "confidence_note": "Test",
            "food_items": [],
            "visual_observations": [],
            "nutrition": None,
        }
        with patch('app._call_gemini_json', return_value=(non_food_response, 'gemini-3.5-flash-lite')):
            resp = self.client.post(
                '/api/predict',
                files={'image': ('obj.jpg', raw, 'image/jpeg')},
            )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data['is_food'])
        self.assertIsNone(data['nutrition'])

#===========================================================================
# Section: test_activity_3_2.py
#===========================================================================

"""
FoodVerse AI — Smart Bridge Activity 3.2 Test Suite
Freshness Classification and Safety Recommendation Logic

Tests:
  01. classify_freshness: Gemini 'fresh'   -> status 'fresh', label 'Fresh'.
  02. classify_freshness: Gemini 'aging'   -> status 'moderately_fresh', label 'Use Soon'.
  03. classify_freshness: Gemini 'spoiled' -> status 'spoiled', label 'Potential Spoilage'.
  04. classify_freshness: blurry image     -> inconclusive before Gemini call.
  05. classify_freshness: underexposed     -> inconclusive before Gemini call.
  06. classify_freshness: overexposed      -> inconclusive before Gemini call.
  07. classify_freshness: gemini_data=None -> inconclusive (Gemini failure path).
  08. classify_freshness: malformed Gemini response (missing required fields) -> inconclusive.
  09. Evidence level: High -> strong, Medium -> moderate, Cautious -> limited, unknown -> insufficient.
  10. safety_recommendations populated for all four status values.
  11. limitations field always present and non-empty in every response.
  12. All required Activity 3.2 response fields present.
  13. Legacy backward-compat fields (checks, observations, certainty, disclaimer, engine) present.
  14. POST /api/freshness returns HTTP 200 with required fields (Gemini mocked).
  15. POST /api/freshness: unsupported file type returns HTTP 415.
  16. POST /api/freshness: blurry image short-circuits Gemini (Gemini NOT called).
  17. Regression: POST /api/predict still functional (Activity 2.1).
  18. Regression: POST /api/freshness returns backward-compatible label / checks / observations.
  19. Unexpected Gemini status value -> inconclusive.
  20. preprocessing_features slim dict present and contains expected keys.
"""

import io
import unittest
import warnings
from unittest.mock import patch, MagicMock

import numpy as np
from PIL import Image

warnings.filterwarnings('ignore', message=r'.*starlette\.testclient.*')

from fastapi.testclient import TestClient

import app
import freshness_service

client = TestClient(app.app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _good_cues(is_blurry: bool = False, exposure: str = "normal") -> dict:
    """Minimal freshness_cues dict matching image_processor schema."""
    return {
        "color_profile": {
            "mean_saturation_pct": 45.0,
            "mean_hue_deg": 90.0,
            "mean_value_pct": 55.0,
            "dominant_tone": "green",
            "channel_means": {"red": 80.0, "green": 130.0, "blue": 70.0},
        },
        "texture_profile": {
            "texture_variation": 20.0,
            "rms_contrast": 15.0,
            "surface_uniformity": "moderate",
        },
        "quality_indicators": {
            "sharpness_score": 5.0 if is_blurry else 250.0,
            "is_blurry": is_blurry,
            "blur_threshold": 100.0,
            "brightness_mean": 30.0 if exposure == "underexposed" else (240.0 if exposure == "overexposed" else 128.0),
            "exposure_quality": exposure,
        },
        "disclaimer": "Visual features are informational only.",
    }


def _gemini_response(status: str = "fresh", certainty: str = "High") -> dict:
    """Minimal valid Gemini freshness response."""
    label_map = {"fresh": "Fresh", "aging": "Use Soon", "spoiled": "Potential Spoilage"}
    return {
        "status": status,
        "label": label_map.get(status, "Unknown"),
        "certainty": certainty,
        "food_item": "Apple",
        "shelf": "5-7 days if refrigerated",
        "observations": {
            "color": "Bright red with no browning.",
            "texture": "Firm skin, no soft spots.",
            "defects": "No visible mold or lesions.",
        },
        "checks": [
            {"ok": True,  "text": "Surface integrity intact."},
            {"ok": True,  "text": "No visible discoloration."},
            {"ok": True,  "text": "No fungal growth detected."},
            {"ok": True,  "text": "Safe for consumption based on visual inspection."},
        ],
        "recommendations": [
            "Store in the refrigerator to extend freshness.",
            "Consume within the estimated shelf window.",
        ],
        "disclaimer": "Visual assessment cannot detect invisible bacteria or toxins.",
    }


def _make_jpeg(width: int = 200, height: int = 200, color: tuple = (180, 120, 60)) -> bytes:
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Unit tests: freshness_service.classify_freshness
# ---------------------------------------------------------------------------

class TestFreshnessServiceUnit(unittest.TestCase):

    def test_01_fresh_status(self):
        """Gemini 'fresh' -> canonical status 'fresh', label 'Fresh'."""
        result = freshness_service.classify_freshness(
            freshness_cues=_good_cues(),
            gemini_data=_gemini_response("fresh"),
            gemini_model_used="gemini-test",
        )
        self.assertEqual(result["status"], "fresh")
        self.assertEqual(result["label"], "Fresh")
        self.assertEqual(result["assessment_method"], "gemini_vision_multimodal")

    def test_02_moderately_fresh_from_aging(self):
        """Gemini 'aging' -> canonical status 'moderately_fresh', label 'Use Soon'."""
        result = freshness_service.classify_freshness(
            freshness_cues=_good_cues(),
            gemini_data=_gemini_response("aging", "Medium"),
            gemini_model_used="gemini-test",
        )
        self.assertEqual(result["status"], "moderately_fresh")
        self.assertEqual(result["label"], "Use Soon")
        self.assertEqual(result["assessment_method"], "gemini_vision_multimodal")

    def test_03_spoiled_status(self):
        """Gemini 'spoiled' -> canonical status 'spoiled', label 'Potential Spoilage'."""
        result = freshness_service.classify_freshness(
            freshness_cues=_good_cues(),
            gemini_data=_gemini_response("spoiled", "Cautious"),
            gemini_model_used="gemini-test",
        )
        self.assertEqual(result["status"], "spoiled")
        self.assertEqual(result["label"], "Potential Spoilage")

    def test_04_blurry_image_inconclusive(self):
        """Blurry image -> inconclusive before Gemini is called."""
        result = freshness_service.classify_freshness(
            freshness_cues=_good_cues(is_blurry=True),
            gemini_data=_gemini_response("fresh"),  # should be ignored
            gemini_model_used="gemini-test",
        )
        self.assertEqual(result["status"], "inconclusive")
        self.assertEqual(result["assessment_method"], "inconclusive_image_quality")

    def test_05_underexposed_image_inconclusive(self):
        """Underexposed image -> inconclusive before Gemini is called."""
        result = freshness_service.classify_freshness(
            freshness_cues=_good_cues(exposure="underexposed"),
            gemini_data=_gemini_response("fresh"),
            gemini_model_used="gemini-test",
        )
        self.assertEqual(result["status"], "inconclusive")
        self.assertEqual(result["assessment_method"], "inconclusive_image_quality")

    def test_06_overexposed_image_inconclusive(self):
        """Overexposed image -> inconclusive before Gemini is called."""
        result = freshness_service.classify_freshness(
            freshness_cues=_good_cues(exposure="overexposed"),
            gemini_data=_gemini_response("fresh"),
            gemini_model_used="gemini-test",
        )
        self.assertEqual(result["status"], "inconclusive")
        self.assertEqual(result["assessment_method"], "inconclusive_image_quality")

    def test_07_gemini_none_inconclusive(self):
        """gemini_data=None -> inconclusive (API failure path)."""
        result = freshness_service.classify_freshness(
            freshness_cues=_good_cues(),
            gemini_data=None,
        )
        self.assertEqual(result["status"], "inconclusive")
        self.assertEqual(result["assessment_method"], "inconclusive_gemini_failure")

    def test_08_malformed_gemini_response(self):
        """Gemini response missing required fields -> inconclusive."""
        incomplete = {"status": "fresh"}  # missing label, certainty, food_item
        result = freshness_service.classify_freshness(
            freshness_cues=_good_cues(),
            gemini_data=incomplete,
        )
        self.assertEqual(result["status"], "inconclusive")
        self.assertEqual(result["assessment_method"], "inconclusive_gemini_failure")

    def test_09_evidence_level_mapping(self):
        """Evidence level maps correctly from Gemini certainty strings."""
        cases = [
            ("High",     "strong"),
            ("Medium",   "moderate"),
            ("Cautious", "limited"),
            ("Unknown",  "insufficient"),
            (None,       "insufficient"),
        ]
        for certainty, expected in cases:
            with self.subTest(certainty=certainty):
                data = _gemini_response("fresh", certainty) if certainty is not None else _gemini_response("fresh")
                if certainty is None:
                    data.pop("certainty", None)
                result = freshness_service.classify_freshness(
                    freshness_cues=_good_cues(),
                    gemini_data=data,
                )
                self.assertEqual(result["evidence_level"], expected,
                                 f"certainty={certainty!r} should map to {expected!r}")

    def test_10_safety_recommendations_all_statuses(self):
        """safety_recommendations is a non-empty list for every canonical status."""
        for gemini_status, cues_kwargs in [
            ("fresh",   {}),
            ("aging",   {}),
            ("spoiled", {}),
        ]:
            with self.subTest(status=gemini_status):
                result = freshness_service.classify_freshness(
                    freshness_cues=_good_cues(**cues_kwargs),
                    gemini_data=_gemini_response(gemini_status),
                )
                self.assertIsInstance(result["safety_recommendations"], list)
                self.assertGreater(len(result["safety_recommendations"]), 0)

        # inconclusive path
        result = freshness_service.classify_freshness(
            freshness_cues=_good_cues(is_blurry=True),
            gemini_data=None,
        )
        self.assertIsInstance(result["safety_recommendations"], list)
        self.assertGreater(len(result["safety_recommendations"]), 0)

    def test_11_limitations_always_present(self):
        """limitations field is present and non-empty in every result."""
        for gemini_data, cues in [
            (_gemini_response("fresh"),   _good_cues()),
            (_gemini_response("aging"),   _good_cues()),
            (_gemini_response("spoiled"), _good_cues()),
            (None,                        _good_cues()),
            (None,                        _good_cues(is_blurry=True)),
        ]:
            result = freshness_service.classify_freshness(
                freshness_cues=cues,
                gemini_data=gemini_data,
            )
            self.assertIn("limitations", result)
            self.assertTrue(result["limitations"], "limitations must be a non-empty string")

    def test_12_required_a32_fields_present(self):
        """All required Activity 3.2 canonical fields are present."""
        required = {
            "status", "label", "assessment_method", "evidence_level",
            "food_item", "shelf", "observed_cues", "safety_recommendations",
            "limitations", "preprocessing_features",
        }
        result = freshness_service.classify_freshness(
            freshness_cues=_good_cues(),
            gemini_data=_gemini_response("fresh"),
        )
        missing = required - result.keys()
        self.assertFalse(missing, f"Missing Activity 3.2 fields: {missing}")

    def test_13_legacy_compat_fields_present(self):
        """Backward-compatible fields (checks, observations, certainty, disclaimer, engine) are present."""
        legacy = {"checks", "observations", "certainty", "disclaimer", "engine"}
        result = freshness_service.classify_freshness(
            freshness_cues=_good_cues(),
            gemini_data=_gemini_response("fresh"),
            gemini_model_used="gemini-test",
        )
        missing = legacy - result.keys()
        self.assertFalse(missing, f"Missing legacy compat fields: {missing}")

    def test_19_unexpected_gemini_status_inconclusive(self):
        """Gemini status value not in known set -> inconclusive."""
        bad_data = _gemini_response("fresh")
        bad_data["status"] = "unknown_value"
        result = freshness_service.classify_freshness(
            freshness_cues=_good_cues(),
            gemini_data=bad_data,
        )
        self.assertEqual(result["status"], "inconclusive")

    def test_20_preprocessing_features_keys(self):
        """preprocessing_features contains expected slim summary keys."""
        expected_keys = {
            "sharpness_score", "is_blurry", "exposure_quality",
            "brightness_mean", "dominant_tone", "mean_saturation_pct", "surface_uniformity",
        }
        result = freshness_service.classify_freshness(
            freshness_cues=_good_cues(),
            gemini_data=_gemini_response("fresh"),
        )
        pf = result["preprocessing_features"]
        self.assertIsInstance(pf, dict)
        missing = expected_keys - pf.keys()
        self.assertFalse(missing, f"preprocessing_features missing keys: {missing}")


# ---------------------------------------------------------------------------
# Integration tests: POST /api/freshness via TestClient
# ---------------------------------------------------------------------------

# Stable prep telemetry returned by mocked preprocess_image_opencv
_MOCK_TELEMETRY = {
    "freshness_cues": _good_cues(),
    "preprocessing_applied": {
        "decoded": True,
        "resized": False,
        "denoised": True,
        "visual_feature_extraction": True,
    },
}
_MOCK_PIL = Image.new("RGB", (200, 200), (180, 120, 60))


class TestFreshnessAPIIntegration(unittest.TestCase):

    def _post_freshness(self, jpeg_bytes: bytes):
        return client.post(
            "/api/freshness",
            files={"image": ("test.jpg", jpeg_bytes, "image/jpeg")},
        )

    @patch("app.preprocess_image_opencv", return_value=(_MOCK_PIL, _MOCK_TELEMETRY))
    @patch("app._call_gemini_json", return_value=(_gemini_response("fresh"), "gemini-test"))
    def test_14_api_returns_200_with_required_fields(self, mock_gemini, mock_prep):
        """POST /api/freshness returns HTTP 200 and all required A3.2 fields."""
        resp = self._post_freshness(_make_jpeg())
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        for field in ("status", "label", "assessment_method", "evidence_level",
                      "food_item", "shelf", "observed_cues", "safety_recommendations",
                      "limitations", "preprocessing_features",
                      "checks", "observations", "disclaimer", "engine"):
            self.assertIn(field, body, f"Missing field in API response: {field}")

    def test_15_unsupported_mime_type_415(self):
        """POST /api/freshness with unsupported MIME type returns HTTP 415."""
        resp = client.post(
            "/api/freshness",
            files={"image": ("test.txt", b"not an image", "text/plain")},
        )
        self.assertEqual(resp.status_code, 415)

    @patch("app.preprocess_image_opencv", return_value=(
        _MOCK_PIL,
        {"freshness_cues": _good_cues(is_blurry=True),
         "preprocessing_applied": {"decoded": True, "resized": False, "denoised": True, "visual_feature_extraction": True}},
    ))
    @patch("app._call_gemini_json")
    def test_16_blurry_image_skips_gemini(self, mock_gemini, mock_prep):
        """Blurry image: endpoint returns inconclusive without calling Gemini."""
        resp = self._post_freshness(_make_jpeg())
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["status"], "inconclusive")
        mock_gemini.assert_not_called()

    @patch("app.preprocess_image_opencv", return_value=(_MOCK_PIL, _MOCK_TELEMETRY))
    @patch("app._call_gemini_json", return_value=(_gemini_response("fresh"), "gemini-test"))
    def test_17_predict_regression(self, mock_gemini, mock_prep):
        """Regression: POST /api/predict (Activity 2.1) still returns HTTP 200."""
        resp = client.post(
            "/api/predict",
            files={"image": ("food.jpg", _make_jpeg(), "image/jpeg")},
        )
        self.assertEqual(resp.status_code, 200)

    @patch("app.preprocess_image_opencv", return_value=(_MOCK_PIL, _MOCK_TELEMETRY))
    @patch("app._call_gemini_json", return_value=(_gemini_response("aging", "Medium"), "gemini-test"))
    def test_18_backward_compat_legacy_fields(self, mock_gemini, mock_prep):
        """
        POST /api/freshness: legacy fields (label, checks, observations, certainty)
        are present for backward-compatible UI rendering.
        """
        resp = self._post_freshness(_make_jpeg())
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        # New canonical field
        self.assertEqual(body["status"], "moderately_fresh")
        # Legacy label should be human-readable
        self.assertIsInstance(body["label"], str)
        self.assertTrue(len(body["label"]) > 0)
        # Legacy pass-through fields
        self.assertIsInstance(body["checks"], list)
        self.assertIsInstance(body["observations"], dict)
        self.assertIn("certainty", body)


if __name__ == "__main__":
    unittest.main(verbosity=2)


if __name__ == "__main__":
    unittest.main()
