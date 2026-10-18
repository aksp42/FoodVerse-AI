"""
FoodVerse AI — FastAPI Backend v3.0
Architecture: React Frontend -> FastAPI Backend -> SQLite DB + AI Models
AI Models:
  - Gemini Vision (Multimodal AI) -> Sole Food Recognition & Visual Nutrition Analysis
  - Gemini Vision (Multimodal AI) -> Food Freshness & Spoilage Detection
  - Gemini Vision (Multimodal AI) -> Restaurant Hygiene & Safety Monitoring
  - Gemini LLM                    -> Smart Cooking Assistant (Pantry-to-Recipe)
  - Gemini LLM                    -> Personalized 7-Day Meal Planner
"""

import io
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional

import numpy as np
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pydantic import BaseModel

import cooking_service
import cv2
import database
import freshness_service
import hygiene_service
import image_processor
import meal_planner_service
import nutrition_service
import profile_service
import video_processor

load_dotenv()

# -- Constants -----------------------------------------------------------------
GEMINI_KEY    = os.getenv('GEMINI_API_KEY', '')
ALLOWED_IMG   = {'image/jpeg', 'image/png', 'image/webp', 'image/gif', 'image/jpg'}
MAX_MB        = 10
MAX_IMG_DIMENSION = 1600  # maximum dimension in pixels for aspect-ratio-preserving downscale
GOAL_CALORIES = {
    'Weight Loss':     1500,
    'Weight Maintain': 1900,
    'Muscle Gain':     2400,
    'Heart Healthy':   1800,
}

# -- Gemini setup (google-genai client) -----------------------------------------
genai_client = None
try:
    from google import genai
    from google.genai import types
    if GEMINI_KEY:
        genai_client = genai.Client(api_key=GEMINI_KEY)
        print('  Gemini Client initialized successfully.', flush=True)
    else:
        print('  [WARN] GEMINI_API_KEY is not set in environment.', flush=True)
except Exception as exc:
    print(f'  [WARN] Could not initialize google-genai client: {exc}', flush=True)

# -- FastAPI App ----------------------------------------------------------------
app = FastAPI(
    title='FoodVerse AI Multimodal API',
    description='Multimodal Food Intelligence Agent — Vision + Audio + LLM',
    version='3.1.0',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# -- OpenCV Preprocessing & Visual Feature Extraction (Activity 3.1) -----------
def preprocess_image_opencv(raw_bytes: bytes) -> tuple[Image.Image, dict]:
    """
    Decodes, validates, normalizes, and extracts visual features from uploaded image bytes
    via OpenCV (cv2) and image_processor module (Activity 3.1):
    1. Rejects empty byte streams (400) or oversized files (413).
    2. Decodes image array using cv2.imdecode with format corruption validation.
    3. Handles 1-channel Grayscale expansion and 4-channel RGBA white-compositing.
    4. Performs aspect-ratio-preserving resize if dimensions exceed MAX_IMG_DIMENSION.
    5. Extracts deterministic visual features (aspect ratio, sharpness, brightness, HSV, texture).
    6. Converts to standard PIL Image for downstream Gemini multimodal vision.
    7. Emits structured telemetry detailing dimensions and visual features.
    """
    return image_processor.preprocess_food_image(raw_bytes, max_dimension=MAX_IMG_DIMENSION)

def _pil_from_bytes(raw: bytes) -> Image.Image:
    pil_img, _ = preprocess_image_opencv(raw)
    return pil_img

def _clean_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE)
    return text.strip()

# List of candidate Gemini models ordered by efficiency and free-tier quota availability
CANDIDATE_MODELS = [
    'gemini-3.5-flash-lite',
    'gemini-3.5-flash',
    'gemini-3.7-flash',
    'gemini-3.8-flash',
]

def _call_gemini_json(prompt: str, image: Optional[Image.Image] = None) -> tuple[dict, str]:
    if genai_client is None:
        raise HTTPException(503, 'Gemini API is unavailable or GEMINI_API_KEY is missing.')
    
    contents = [prompt]
    if image is not None:
        contents.append(image)

    last_error = None
    for model_name in CANDIDATE_MODELS:
        try:
            response = genai_client.models.generate_content(
                model=model_name,
                contents=contents
            )
            cleaned = _clean_json(response.text)
            return json.loads(cleaned), model_name
        except json.JSONDecodeError:
            last_error = f"{model_name} returned non-JSON response"
            continue
        except Exception as exc:
            err_str = str(exc)
            last_error = err_str
            # Check for 429 quota exhaustion or rate limits, and cascade to next model
            if any(term in err_str for term in ['429', 'RESOURCE_EXHAUSTED', 'ResourceExhausted', 'quota', '404', 'NOT_FOUND']):
                print(f'  [FAILOVER] {model_name} quota/availability issue. Failing over to next candidate...', flush=True)
                continue
            raise HTTPException(502, f'Gemini API call failed ({model_name}): {err_str}')

    raise HTTPException(429, f'All Gemini candidate models exceeded rate limits/quota: {last_error}')

# ===============================================================================
# API Routes
# ===============================================================================

@app.get('/api/health')
def health():
    return {
        'status': 'ok',
        'backend': 'FastAPI',
        'image_preprocessor': (
            f'OpenCV {cv2.__version__} — Activity 3.1: decode, normalize (Grayscale/RGBA), '
            'aspect-preserving resize, Laplacian sharpness, Rec.601 luminance, HSV color, Sobel texture'
        ),
        'visual_feature_extraction': (
            'Activity 3.1 — aspect_ratio, orientation, sharpness_score, is_blurry, '
            'brightness_mean, exposure_quality, mean_saturation, texture_variation, rms_contrast, freshness_cues'
        ),
        'primary_food_recognition': f'Gemini Vision ({CANDIDATE_MODELS[0]} with smart quota failover)',
        'nutrition_estimation': 'Hierarchical Reference (ICMR-NIN IFCT 2017 & USDA FDC) + Deterministic Health Scoring (0-100)',
        'freshness_detector': f'Gemini Vision ({CANDIDATE_MODELS[0]})',
        'hygiene_monitor': f'Gemini Multimodal ({CANDIDATE_MODELS[0]})',
        'cooking_assistant': f'Gemini LLM ({CANDIDATE_MODELS[0]})',
        'meal_planner': f'Gemini LLM ({CANDIDATE_MODELS[0]})',
        'active_models': CANDIDATE_MODELS,
        'gemini_available': genai_client is not None,
        'database': 'SQLite active (Real Data Persistence)'
    }

# -- 1. Food Recognition & Nutrition (PRIMARY: Gemini Vision + OpenCV) -----------
@app.post('/api/predict')
async def predict_food(image: UploadFile = File(...), engine: Optional[str] = Form(None)):
    """
    Primary Food Image Detection & Classification (Smart Bridge Activity 2.1):
    1. Validates upload format, file size, and non-empty content.
    2. Decodes and preprocesses image with OpenCV (BGR->RGB, aspect-preserving resize).
    3. Ingests preprocessed image into Google Gemini Multimodal Vision.
    4. Accurately distinguishes food from non-food or ambiguous objects.
    5. Returns structured classification, visible ingredients, and nutrition profile.
    6. Logs event to SQLite persistence.
    """
    # 1. Content-Type validation
    content_type = (image.content_type or '').lower()
    if content_type and content_type not in ALLOWED_IMG:
        raise HTTPException(415, 'Unsupported file format. Please upload JPG, PNG, or WebP.')

    # 2. Ingestion & size validation
    raw = await image.read()
    if not raw or len(raw) == 0:
        raise HTTPException(400, 'Empty image file uploaded. Please upload a valid food photo.')
    if len(raw) > MAX_MB * 1024 * 1024:
        raise HTTPException(413, f'Image too large. Limit is {MAX_MB}MB.')

    # 3. OpenCV decoding, validation & preprocessing
    pil, prep_telemetry = preprocess_image_opencv(raw)

    # 4. Multimodal Food Classification Prompt
    prompt = """You are an expert food scientist and culinary computer vision AI.
Analyze this photograph carefully.

Step 1: First determine whether this image actually contains recognizable food, prepared dishes, fresh produce, snacks, or groceries.
- If the image contains clearly non-food subjects (e.g., furniture, electronic devices, people with no food, landscapes, vehicles, documents, text screenshots, empty plates/bowls with no food, pets), set "is_food": false.
- If the image is ambiguous or you cannot identify any edible item, set "is_food": false.
- If the image clearly contains one or more prepared dishes, fresh produce, or food items, set "is_food": true.

Step 2: Return ONLY a valid JSON object adhering strictly to the schema below.

If "is_food": true, return:
{
  "is_food": true,
  "predicted_class": "<exact common name of primary dish/food item, e.g. Chole Bhature, Paneer Butter Masala, Masala Dosa, Apple>",
  "description": "<concise 1-2 sentence description of visual appearance, preparation style, and culinary context>",
  "confidence": "High" | "Medium" | "Low",
  "confidence_score": <model-estimated float between 0.50 and 0.99 reflecting visual distinctiveness>,
  "confidence_note": "Model-estimated visual confidence based on distinctive culinary features and visual clarity",
  "food_items": [
    "<ingredient, visible condiment, or component 1>",
    "<ingredient, visible condiment, or component 2>"
  ],
  "visual_observations": [
    "<specific visual cue, e.g. golden-brown crisp crust, rich spiced gravy>",
    "<visible garnish or side, e.g. chopped cilantro, lemon wedge, onions>",
    "<cooking method detected, e.g. deep fried, simmered curry, tandoor roasted>"
  ],
  "nutrition": {
    "serving": "<standard realistic serving portion assumption, e.g. 1 plate (approx 250g)>",
    "calories": <estimated integer calories per serving>,
    "protein": <estimated integer grams of protein>,
    "carbs": <estimated integer grams of carbs>,
    "fat": <estimated integer grams of fat>,
    "fiber": <estimated integer grams of fiber>,
    "tip": "<practical dietary guidance regarding portion, glycemic balance, or sodium>"
  }
}

If "is_food": false, return:
{
  "is_food": false,
  "predicted_class": "Unrecognized Non-Food Object",
  "description": "<brief description of what is actually visible instead of food, e.g. electronic device, furniture, empty surface>",
  "confidence": "Low",
  "confidence_score": 0.15,
  "confidence_note": "Visual analysis did not detect recognizable culinary items or edible dishes",
  "food_items": [],
  "visual_observations": [
    "<objective visual observation of non-food elements detected in the scene>"
  ],
  "nutrition": null
}

Guidelines:
- Return ONLY the raw valid JSON object without markdown formatting.
- Do NOT hallucinate dish names for non-food objects.
- Clearly differentiate model-estimated confidence from calibrated laboratory probability."""

    data, model_used = _call_gemini_json(prompt, pil)

    # 5. Schema Normalization & Defense-in-Depth
    is_food = bool(data.get('is_food', True))
    default_name = 'Unknown Food' if is_food else 'Unrecognized Non-Food Object'
    food_name = str(data.get('predicted_class') or data.get('food_name') or default_name)

    conf_str = str(data.get('confidence') or data.get('certainty') or ('High' if is_food else 'Low'))
    if conf_str not in {'High', 'Medium', 'Low'}:
        conf_str = 'Medium' if is_food else 'Low'

    conf_score = data.get('confidence_score')
    if conf_score is None or not isinstance(conf_score, (int, float)):
        conf_score = 0.90 if conf_str == 'High' else (0.75 if conf_str == 'Medium' else 0.20)
    conf_score = float(conf_score)

    food_items = data.get('food_items') or data.get('ingredients') or []
    if not isinstance(food_items, list):
        food_items = [str(food_items)]

    visual_obs = data.get('visual_observations') or []
    if not isinstance(visual_obs, list):
        visual_obs = [str(visual_obs)]

    # 5. Nutrition Estimation & Deterministic Health Scoring (Smart Bridge Activity 2.2)
    final_nutrition = nutrition_service.estimate_nutrition_and_score(
        food_name=food_name,
        food_items=food_items,
        gemini_raw_nutrition=data.get('nutrition'),
        is_food=is_food
    )

    # Normalized response
    response_payload = {
        'success': True,
        'is_food': is_food,
        'food_name': food_name,
        'predicted_class': food_name,  # preserved for backwards compatibility
        'confidence': conf_str,
        'confidence_score': conf_score,
        'confidence_note': data.get('confidence_note') or 'Model-estimated visual confidence',
        'certainty': conf_str,  # preserved for existing UI
        'description': data.get('description', ''),
        'food_items': food_items,
        'visual_observations': visual_obs,
        'nutrition': final_nutrition,
        'preprocessing_applied': prep_telemetry,
        'engine': f'{model_used} Vision (Multimodal AI)'
    }

    # 6. Database Logging
    if is_food:
        nut = response_payload.get('nutrition') or {}
        cals = nut.get('calories', 0) if isinstance(nut, dict) else 0
        database.log_activity(
            "food",
            f"Identified {food_name}",
            {"calories": cals, "nutrition": nut, "engine": response_payload['engine'], "is_food": True}
        )
    else:
        database.log_activity(
            "food",
            f"Scan: {food_name}",
            {"calories": 0, "nutrition": None, "engine": response_payload['engine'], "is_food": False}
        )

    return response_payload

# -- 2. Food Freshness & Spoilage Detection (Activity 3.2: Gemini Vision + Classification) ----
@app.post('/api/freshness')
async def freshness_analysis(image: UploadFile = File(...)):
    """
    Multimodal freshness and spoilage assessment — Activity 3.2.

    Pipeline:
      1. Validate MIME type.
      2. Run Activity 3.1 preprocessing to obtain PIL image + freshness_cues telemetry.
      3. Pre-check image quality; return inconclusive early for blurry/bad-exposure images.
      4. Call Gemini Vision for multimodal freshness assessment; catch all failures.
      5. Delegate classification to freshness_service.classify_freshness().
      6. Log result to SQLite and return structured response.

    Response always contains Activity 3.2 fields:
      status (fresh|moderately_fresh|spoiled|inconclusive), label, assessment_method,
      evidence_level, observed_cues, safety_recommendations, limitations, preprocessing_features,
      plus backward-compatible legacy fields (checks, observations, certainty, recommendations).
    """
    if image.content_type not in ALLOWED_IMG:
        raise HTTPException(415, 'Unsupported file format.')

    raw = await image.read()

    # Step 2 — Preprocess and extract Activity 3.1 freshness_cues telemetry
    pil, prep_telemetry = preprocess_image_opencv(raw)
    freshness_cues: dict = prep_telemetry.get("freshness_cues", {})

    # Step 3 — Image quality pre-check (handled inside freshness_service)
    # Pass freshness_cues to classify_freshness; it will return inconclusive early
    # if quality_indicators indicate blurry or bad exposure — no Gemini call needed.
    quality = freshness_cues.get("quality_indicators", {})
    is_blurry       = bool(quality.get("is_blurry", False))
    exposure_quality = str(quality.get("exposure_quality", "normal"))

    gemini_data:   dict | None = None
    model_used:    str         = ""

    if not is_blurry and exposure_quality == "normal":
        # Step 4 — Gemini Vision multimodal assessment
        prompt = """You are a certified food safety analyst AI.
Perform a cautious visual freshness evaluation of this food/produce photograph.

Return ONLY a valid JSON object matching this schema:
{
  "status": "fresh" | "aging" | "spoiled",
  "label": "Fresh" | "Use Soon" | "Potential Spoilage",
  "certainty": "High" | "Medium" | "Cautious",
  "food_item": "<name of food item detected>",
  "shelf": "<cautious estimated shelf life, e.g., '3-4 days if refrigerated'>",
  "observations": {
    "color": "<visual observation of coloration or browning>",
    "texture": "<visual observation of firmness, wilting, bruising, or moisture>",
    "defects": "<presence or absence of surface fungal spores, dark spots, or decay>"
  },
  "checks": [
    {"ok": true/false, "text": "<observation 1 on surface integrity>"},
    {"ok": true/false, "text": "<observation 2 on discoloration>"},
    {"ok": true/false, "text": "<observation 3 on microbial/mold risk>"},
    {"ok": true/false, "text": "<observation 4 on consumption safety recommendation>"}
  ],
  "recommendations": [
    "<actionable storage or consumption step 1>",
    "<actionable storage or consumption step 2>"
  ],
  "disclaimer": "Visual assessment cannot detect invisible bacteria or toxins. When in doubt, discard."
}

Rules:
- Be conservative. If mold, sliminess, or significant rot is visible, label MUST be 'Potential Spoilage'.
- If signs of softening or past peak freshness exist without rot, status is 'aging' / 'Use Soon'."""

        try:
            gemini_data, model_used = _call_gemini_json(prompt, pil)
        except Exception:
            # Gemini unavailable or failed — freshness_service will return inconclusive
            gemini_data  = None
            model_used   = ""

    # Step 5 — Activity 3.2 classification
    result = freshness_service.classify_freshness(
        freshness_cues=freshness_cues,
        gemini_data=gemini_data,
        gemini_model_used=model_used,
    )

    # Step 6 — Database logging using normalised status
    database.log_activity(
        "freshness",
        f"Freshness: {result.get('food_item', 'Produce')} ({result.get('label')})",
        {
            "status":             result.get("status"),
            "label":              result.get("label"),
            "assessment_method":  result.get("assessment_method"),
            "evidence_level":     result.get("evidence_level"),
            "engine":             result.get("engine"),
        },
    )
    return result

# -- 3. Restaurant Hygiene & Kitchen Safety (Activity 4.1) --------------------
_HYGIENE_GEMINI_PROMPT = """You are a certified commercial kitchen and food safety hygiene inspector AI.
Inspect this kitchen or food preparation area image carefully.

Return ONLY a valid JSON object with this schema:
{
  "observations": [
    {
      "indicator": "surface_cleanliness",
      "status": "observed" | "not_observed" | "uncertain",
      "evidence": "<what you can see that supports this assessment>"
    },
    {
      "indicator": "food_handling_practices",
      "status": "observed" | "not_observed" | "uncertain",
      "evidence": "<what you can see>"
    },
    {
      "indicator": "cross_contamination_risk",
      "status": "observed" | "not_observed" | "uncertain",
      "evidence": "<what you can see>"
    },
    {
      "indicator": "gloves_ppe",
      "status": "observed" | "not_observed" | "uncertain",
      "evidence": "<what you can see — if hands not visible, use uncertain>"
    },
    {
      "indicator": "hair_coverings",
      "status": "observed" | "not_observed" | "uncertain",
      "evidence": "<what you can see — if no person visible, use uncertain>"
    },
    {
      "indicator": "waste_management",
      "status": "observed" | "not_observed" | "uncertain",
      "evidence": "<what you can see>"
    }
  ],
  "frame_summary": "<one sentence summary of visible hygiene conditions>"
}

Rules:
- Use "uncertain" when an indicator is not visible or the image is too dark/blurry to assess.
- Do NOT label something "not_observed" solely because it is absent from view — only use "not_observed" when you can positively confirm the indicator is absent (e.g., gloves clearly missing while food handling is occurring).
- Do NOT fabricate observations. Only describe what is genuinely visible."""


@app.post('/api/hygiene')
async def hygiene_inspection(image: UploadFile = File(...)):
    """
    Restaurant hygiene and kitchen safety analysis — Activity 4.1.

    Accepts kitchen images (JPEG/PNG/WebP) or video clips (MP4/WebM/MOV).

    Image path:
      1. Preprocess via Activity 3.1 pipeline.
      2. Single Gemini Vision call with structured indicator prompt.
      3. Score via hygiene_service.calculate_compliance_score().

    Video path:
      1. Extract representative frames via video_processor.extract_frames().
      2. Call Gemini Vision for each frame with structured indicator prompt.
      3. Aggregate observations across frames (worst-case per indicator).
      4. Score via hygiene_service.calculate_compliance_score().

    Response: backward-compatible (score, grade, findings, actionable_corrections)
    plus Activity 4.1 fields (compliance_score, assessable_indicators, coverage,
    score_breakdown, alerts, uncertain_indicators, observations, limitations).
    """
    allowed = ALLOWED_IMG | video_processor.SUPPORTED_VIDEO_TYPES
    if image.content_type not in allowed:
        raise HTTPException(415, 'Unsupported file format. Use JPEG/PNG/WebP images or MP4/WebM/MOV video.')

    raw          = await image.read()
    content_type = image.content_type
    is_video     = content_type in video_processor.SUPPORTED_VIDEO_TYPES

    all_observations: list = []
    frames_telemetry: dict | None = None
    model_used: str = ""

    if is_video:
        # --- Video path: extract frames, call Gemini per frame ---------------
        frames, frames_telemetry = video_processor.extract_frames(
            raw_bytes=raw,
            content_type=content_type,
        )
        for ts, pil_frame in frames:
            try:
                gemini_data, used = _call_gemini_json(_HYGIENE_GEMINI_PROMPT, pil_frame)
                model_used = model_used or used
                parsed = hygiene_service.parse_frame_observations(gemini_data, ts)
                all_observations.extend(parsed)
            except Exception:
                # Gemini failure for this frame — skip, continue with others
                pass

    else:
        # --- Image path: single Gemini call ----------------------------------
        pil, _ = preprocess_image_opencv(raw)
        try:
            gemini_data, model_used = _call_gemini_json(_HYGIENE_GEMINI_PROMPT, pil)
            all_observations = hygiene_service.parse_frame_observations(gemini_data, 0.0)
        except Exception:
            gemini_data = None

    # --- Score and build response -------------------------------------------
    score_result = hygiene_service.calculate_compliance_score(all_observations)
    result = hygiene_service.build_hygiene_result(
        score_result=score_result,
        all_observations=all_observations,
        frames_telemetry=frames_telemetry,
        gemini_model_used=model_used,
        media_type="video" if is_video else "image",
    )

    database.log_activity(
        "hygiene",
        f"Hygiene Audit: Score {result['compliance_score']}/100 ({result['grade']}) [{result['media_type']}]",
        {
            "compliance_score":      result["compliance_score"],
            "grade":                 result["grade"],
            "assessable_indicators": result["assessable_indicators"],
            "coverage":              result["coverage"],
            "alert_count":           len(result["alerts"]),
            "media_type":            result["media_type"],
            "engine":                result["engine"],
        },
    )
    return result


# -- 4. Smart Cooking Assistant (Activity 4.2: Gemini Reasoning & Recipe Generation) ---
class CookingRequest(BaseModel):
    ingredients: List[str]
    diet: str = 'Vegetarian'
    servings: int = 2
    cuisine: Optional[str] = 'Indian'
    max_time_mins: Optional[int] = 30
    skill_level: Optional[str] = 'Beginner'
    cooking_objective: Optional[str] = None
    intended_dish: Optional[str] = None
    visual_identified_ingredients: Optional[List[str]] = None

@app.post('/api/cooking')
async def generate_recipe(req: CookingRequest):
    """
    Generates a personalized, structured recipe using Gemini AI reasoning (Activity 4.2).
    Includes cooking tips, doneness cues, safety reminders, and prep/cook timing.
    """
    cleaned_ingredients = [i.strip() for i in req.ingredients if i and i.strip()]
    if not cleaned_ingredients:
        raise HTTPException(400, 'Please provide at least one available ingredient.')

    prompt = cooking_service.build_recipe_prompt(
        ingredients=cleaned_ingredients,
        diet=req.diet,
        servings=req.servings,
        cuisine=req.cuisine or 'Indian',
        max_time_mins=req.max_time_mins or 30,
        skill_level=req.skill_level or 'Beginner',
        cooking_objective=req.cooking_objective,
        intended_dish=req.intended_dish,
        visual_identified_ingredients=req.visual_identified_ingredients,
    )

    try:
        raw_data, model_used = _call_gemini_json(prompt)
    except Exception as exc:
        raise HTTPException(502, f"Gemini recipe generation failed: {exc}")

    normalized = cooking_service.normalize_recipe_response(
        raw_data=raw_data,
        requested_servings=req.servings,
        requested_diet=req.diet,
        cuisine=req.cuisine or 'Indian',
        model_used=model_used,
        visual_identified_ingredients=req.visual_identified_ingredients,
    )

    database.log_activity("cooking", f"Cooked: {normalized.get('name')}", normalized)
    return normalized


@app.post('/api/cooking/detect-ingredients')
async def detect_ingredients_from_image(image: UploadFile = File(...)):
    """
    Identifies visual ingredients from an uploaded photograph of produce/pantry items (Activity 4.2).
    Accepts valid images, preprocesses via OpenCV, and passes to Gemini Vision.
    """
    if image.content_type not in ALLOWED_IMG:
        raise HTTPException(415, 'Unsupported file format. Please upload a JPEG, PNG, or WebP image.')

    raw = await image.read()
    if not raw:
        raise HTTPException(400, 'Empty image upload.')

    pil, _ = preprocess_image_opencv(raw)
    prompt = cooking_service.build_ingredient_vision_prompt()

    try:
        data, model_used = _call_gemini_json(prompt, pil)
    except Exception as exc:
        raise HTTPException(502, f"Gemini ingredient vision analysis failed: {exc}")

    if not isinstance(data, dict):
        data = {}

    detected = data.get("detected_ingredients")
    if not isinstance(detected, list):
        detected = []

    return {
        "is_food": bool(data.get("is_food", len(detected) > 0)),
        "detected_ingredients": [str(x).strip() for x in detected if str(x).strip()],
        "observations": str(data.get("observations") or "Ingredient inspection completed."),
        "confidence_note": str(data.get("confidence_note") or "Visual detection reflects clearly visible items only."),
        "engine": f"{model_used} Vision",
    }

# -- User Profile, Goal & Preference Processing (Activity 5.1) ----------------
class UserProfilePayload(BaseModel):
    user_id: Optional[str] = 'default_user'
    name: Optional[str] = ''
    phone: Optional[str] = ''
    age: Optional[int] = None
    gender: Optional[str] = 'unspecified'
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    diet: Optional[str] = 'Vegetarian'
    goal: Optional[str] = 'Weight Maintain'
    activity_level: Optional[str] = 'moderately active'
    budget: Optional[str] = 'Medium'
    allergies: Optional[Any] = []
    intolerances: Optional[Any] = []
    dislikes: Optional[Any] = []
    restrictions: Optional[Any] = []

@app.post('/api/profile')
async def update_user_profile(payload: UserProfilePayload):
    """
    Validates, normalizes, and saves the user profile and health preferences (Activity 5.1).
    Distinguishes allergies from dislikes and intolerances, and computes Mifflin-St Jeor target.
    """
    raw_dict = payload.model_dump()
    user_id = str(raw_dict.pop('user_id', None) or 'default_user').strip()

    normalized, errors = profile_service.validate_and_normalize_profile(raw_dict)
    if errors:
        raise HTTPException(400, detail={"message": "Profile validation failed", "errors": errors})

    saved = database.save_user_profile(user_id, normalized)
    if not saved:
        raise HTTPException(500, "Failed to persist user profile in database.")

    return {
        "user_id": user_id,
        "profile": normalized,
        "status": "saved"
    }

@app.get('/api/profile')
async def fetch_user_profile(user_id: str = 'default_user'):
    """
    Retrieves the persisted user profile from SQLite (Activity 5.1).
    """
    profile = database.get_user_profile(user_id)
    if not profile:
        # Return sensible clean defaults if not yet customized
        default_profile, _ = profile_service.validate_and_normalize_profile({"diet": "Vegetarian", "goal": "Weight Maintain"})
        return {"user_id": user_id, "profile": default_profile, "is_new": True}
    return {"user_id": user_id, "profile": profile, "is_new": False}


# -- 5. Personalized Meal Planner (Gemini LLM) ---------------------------------
class MealPlanRequest(BaseModel):
    user_id: Optional[str] = 'default_user'
    diet: Optional[str] = None
    goal: Optional[str] = None
    budget: Optional[str] = 'Medium'
    allergies: Optional[str] = ''
    days: int = 7

@app.post('/api/meal-plan')
async def create_meal_plan(req: MealPlanRequest):
    """
    Constructs an authentic, personalized daily or 7-day nutritional meal schedule based on
    user profile, goals, budget, allergies, and dietary preferences (Activity 5.1 & 5.2).
    Enforces deterministic allergen safety, calculates macronutrient totals, and provides
    adaptive recommendations without medical claims.
    """
    days = 1 if req.days == 1 else 7
    stored_profile = database.get_user_profile(req.user_id or 'default_user') or {}
    diet = req.diet or stored_profile.get('diet') or 'Vegetarian'
    goal = req.goal or stored_profile.get('goal') or 'Weight Maintain'
    budget = req.budget or stored_profile.get('budget') or 'Medium'

    prompt, target_cal = meal_planner_service.build_meal_plan_prompt(
        profile=stored_profile,
        diet=diet,
        goal=goal,
        budget=budget,
        allergies=req.allergies,
        days=days,
    )

    try:
        raw_data, model_used = _call_gemini_json(prompt)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI meal plan generation failed: {exc}")

    normalized = meal_planner_service.normalize_meal_plan_response(
        raw_data=raw_data,
        user_profile=stored_profile,
        diet=diet,
        goal=goal,
        budget=budget,
        days_count=days,
        target_cal=target_cal,
    )
    normalized['engine'] = f'{model_used} LLM'
    
    # Persist to database
    database.save_meal_plan_db(diet, goal, budget, normalized)
    database.log_activity(
        "plan",
        f"Generated {normalized['plan_type'].title()} Plan: {diet} ({goal})",
        {"calories": target_cal, "engine": normalized['engine'], "days": days}
    )
    return normalized

@app.get('/api/meal-plan')
async def get_saved_meal_plan(user_id: str = 'default_user'):
    """
    Retrieves the most recently saved meal plan from SQLite (Activity 5.2).
    """
    plan = database.get_latest_meal_plan()
    if not plan:
        return {"plan": None, "message": "No saved meal plan found"}
    return {"plan": plan, "message": "Retrieved latest saved meal plan"}

# -- Real Dashboard & Activity APIs --------------------------------------------
@app.get('/api/dashboard/stats')
def get_dashboard_metrics():
    """
    Returns actual KPI counts, real weekly calorie logs, and real macronutrient split from SQLite.
    No hardcoded fake numbers.
    """
    return database.get_dashboard_summary()

@app.get('/api/activities')
def list_activities(limit: int = 25):
    """
    Returns real logged activities from database.
    """
    return database.get_recent_activities(limit)

# -- Production SPA Static Hosting (Active when frontend_dist exists) ----------
frontend_dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend_dist')
if os.path.isdir(frontend_dist_dir):
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    assets_dir = os.path.join(frontend_dist_dir, 'assets')
    if os.path.isdir(assets_dir):
        app.mount('/assets', StaticFiles(directory=assets_dir), name='assets')

    @app.get('/{full_path:path}')
    async def serve_spa(full_path: str):
        if full_path.startswith(('api/', 'docs', 'openapi.json', 'redoc')):
            raise HTTPException(status_code=404, detail='Not Found')
        file_path = os.path.join(frontend_dist_dir, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist_dir, 'index.html'))


if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get('PORT', 8000))
    uvicorn.run('app:app', host='0.0.0.0', port=port, reload=False)

