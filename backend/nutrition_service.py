"""
FoodVerse AI — Nutrition Estimation and Health Scoring Service
Milestone 2, Activity 2.2

Provides:
  1. Documented nutritional reference database grounded in ICMR-NIN Indian Food
     Composition Tables (IFCT 2017) and USDA FoodData Central (FDC).
  2. Hierarchical estimation: Reference Matching -> Portion Scaling -> AI Visual Estimation.
  3. Validation and sanitization for non-negative, finite nutrient values.
  4. Deterministic, transparent single-serving Health Scoring (0-100 scale).
  5. Actionable, non-medical dietary insights and pairing suggestions.
"""

from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Tuple


# ===============================================================================
# 1. Documented Nutritional Reference Database
# Provenance:
#   - Primary: ICMR - National Institute of Nutrition: Indian Food Composition Tables (IFCT 2017)
#   - Secondary: USDA FoodData Central (FDC) Standard Reference Legacy
# ===============================================================================

NUTRITION_REFERENCE_DB: Dict[str, Dict[str, Any]] = {
    # ── Indian Curries, Breads & Traditional Meals ──
    "chole_bhature": {
        "canonical_name": "Chole Bhature",
        "aliases": ["chole bhature", "chole bhatura", "chola bhatura", "chana bhatura", "chole_bhature"],
        "category": "Curry & Fried Bread",
        "serving_g": 280,
        "serving_desc": "1 plate (2 bhature + 180g chole)",
        "calories": 520,
        "protein": 14.5,
        "carbs": 68.0,
        "fat": 22.0,
        "fiber": 8.5,
        "source": "Standardized Recipe Estimate based on ICMR-NIN Indian Food Composition Tables (IFCT 2017) [Cereal & Legume Preparations]",
    },
    "masala_dosa": {
        "canonical_name": "Masala Dosa",
        "aliases": ["masala dosa", "dosa", "plain dosa", "mysore masala dosa", "masaladosa"],
        "category": "Fermented Cereal & Legume Crepe",
        "serving_g": 200,
        "serving_desc": "1 medium dosa with spiced potato filling & sambar",
        "calories": 350,
        "protein": 6.8,
        "carbs": 52.0,
        "fat": 13.0,
        "fiber": 4.2,
        "source": "Standardized Recipe Estimate based on ICMR-NIN Indian Food Composition Tables (IFCT 2017)",
    },
    "idli_sambar": {
        "canonical_name": "Idli with Sambar",
        "aliases": ["idli", "idli sambar", "idlis", "steamed rice cake"],
        "category": "Fermented Steamed Cereal",
        "serving_g": 220,
        "serving_desc": "2 idlis (100g) + 1 bowl vegetable sambar (120g)",
        "calories": 210,
        "protein": 7.2,
        "carbs": 40.5,
        "fat": 2.2,
        "fiber": 4.8,
        "source": "Standardized Recipe Estimate based on ICMR-NIN Indian Food Composition Tables (IFCT 2017)",
    },
    "paneer_butter_masala": {
        "canonical_name": "Paneer Butter Masala",
        "aliases": ["paneer butter masala", "paneer makhani", "shahi paneer", "paneer gravy", "paneer curry"],
        "category": "Dairy / Cottage Cheese Curry",
        "serving_g": 220,
        "serving_desc": "1 bowl (~220g curry)",
        "calories": 380,
        "protein": 14.0,
        "carbs": 16.0,
        "fat": 29.0,
        "fiber": 2.8,
        "source": "Standardized Recipe Estimate based on ICMR-NIN Indian Food Composition Tables (IFCT 2017) & Culinary Composition",
    },
    "palak_paneer": {
        "canonical_name": "Palak Paneer",
        "aliases": ["palak paneer", "saag paneer", "spinach paneer"],
        "category": "Vegetable & Dairy Curry",
        "serving_g": 230,
        "serving_desc": "1 bowl (~230g spinach gravy with paneer)",
        "calories": 290,
        "protein": 15.5,
        "carbs": 12.0,
        "fat": 20.0,
        "fiber": 5.8,
        "source": "Standardized Recipe Estimate based on ICMR-NIN Indian Food Composition Tables (IFCT 2017)",
    },
    "dal_tadka": {
        "canonical_name": "Dal Tadka",
        "aliases": ["dal tadka", "yellow dal", "toor dal", "dal fry", "dal"],
        "category": "Legume Lentil Soup",
        "serving_g": 200,
        "serving_desc": "1 medium bowl (approx 200g)",
        "calories": 185,
        "protein": 9.5,
        "carbs": 26.0,
        "fat": 5.0,
        "fiber": 5.2,
        "source": "Standardized Recipe Estimate based on ICMR-NIN Indian Food Composition Tables (IFCT 2017) [Code: Pulses]",
    },
    "dal_makhani": {
        "canonical_name": "Dal Makhani",
        "aliases": ["dal makhani", "makhani dal", "black dal", "urad dal makhani"],
        "category": "Legume & Cream Curry",
        "serving_g": 220,
        "serving_desc": "1 medium bowl (approx 220g)",
        "calories": 310,
        "protein": 11.0,
        "carbs": 32.0,
        "fat": 15.5,
        "fiber": 6.8,
        "source": "Standardized Recipe Estimate based on ICMR-NIN Indian Food Composition Tables (IFCT 2017)",
    },
    "rajma_chawal": {
        "canonical_name": "Rajma Chawal",
        "aliases": ["rajma chawal", "rajma", "kidney bean curry with rice"],
        "category": "Legume & Rice Platter",
        "serving_g": 350,
        "serving_desc": "1 plate (150g rice + 200g rajma curry)",
        "calories": 440,
        "protein": 14.2,
        "carbs": 76.0,
        "fat": 8.0,
        "fiber": 9.4,
        "source": "Standardized Recipe Estimate based on ICMR-NIN Indian Food Composition Tables (IFCT 2017)",
    },
    "biryani": {
        "canonical_name": "Vegetable Biryani",
        "aliases": ["biryani", "veg biryani", "vegetable biryani", "pulao", "hyderabadi biryani"],
        "category": "Spiced Rice & Vegetable Platter",
        "serving_g": 300,
        "serving_desc": "1 standard plate (~300g)",
        "calories": 420,
        "protein": 8.5,
        "carbs": 66.0,
        "fat": 14.0,
        "fiber": 4.5,
        "source": "Standardized Recipe Estimate based on ICMR-NIN Indian Food Composition Tables (IFCT 2017)",
    },
    "pav_bhaji": {
        "canonical_name": "Pav Bhaji",
        "aliases": ["pav bhaji", "pavbhaji", "bhaji pav"],
        "category": "Vegetable Mash & Bread",
        "serving_g": 280,
        "serving_desc": "2 buttered pavs + 180g vegetable bhaji",
        "calories": 450,
        "protein": 8.8,
        "carbs": 62.0,
        "fat": 19.0,
        "fiber": 6.0,
        "source": "Standardized Recipe Estimate based on ICMR-NIN Indian Food Composition Tables (IFCT 2017)",
    },
    "vada_pav": {
        "canonical_name": "Vada Pav",
        "aliases": ["vada pav", "vadapav", "wada pav", "batata vada pav"],
        "category": "Street Food / Potato Fritter Bun",
        "serving_g": 140,
        "serving_desc": "1 vada pav with chutneys (140g)",
        "calories": 290,
        "protein": 5.2,
        "carbs": 42.0,
        "fat": 11.5,
        "fiber": 3.0,
        "source": "Standardized Recipe Estimate based on ICMR-NIN Indian Food Composition Tables (IFCT 2017)",
    },
    "samosa": {
        "canonical_name": "Samosa",
        "aliases": ["samosa", "singhara", "aloo samosa"],
        "category": "Fried Savory Pastry",
        "serving_g": 90,
        "serving_desc": "1 piece (~90g)",
        "calories": 240,
        "protein": 3.8,
        "carbs": 26.0,
        "fat": 13.5,
        "fiber": 2.2,
        "source": "Standardized Recipe Estimate based on ICMR-NIN Indian Food Composition Tables (IFCT 2017)",
    },
    "pakora": {
        "canonical_name": "Mixed Vegetable Pakora",
        "aliases": ["pakora", "pakoda", "bhajiya", "fritters", "onion pakoda", "paneer pakora"],
        "category": "Fried Vegetable Fritters",
        "serving_g": 120,
        "serving_desc": "1 small plate (approx 5-6 pieces, 120g)",
        "calories": 280,
        "protein": 5.5,
        "carbs": 28.0,
        "fat": 16.5,
        "fiber": 3.4,
        "source": "Standardized Recipe Estimate based on ICMR-NIN Indian Food Composition Tables (IFCT 2017)",
    },
    "dhokla": {
        "canonical_name": "Khaman Dhokla",
        "aliases": ["dhokla", "khaman", "khaman dhokla"],
        "category": "Steamed Fermented Snack",
        "serving_g": 140,
        "serving_desc": "4 pieces (~140g)",
        "calories": 190,
        "protein": 6.8,
        "carbs": 30.0,
        "fat": 4.5,
        "fiber": 3.5,
        "source": "Standardized Recipe Estimate based on ICMR-NIN Indian Food Composition Tables (IFCT 2017)",
    },
    "poha": {
        "canonical_name": "Kanda Poha",
        "aliases": ["poha", "kanda poha", "flattened rice", "batata poha"],
        "category": "Cooked Breakfast Cereal",
        "serving_g": 180,
        "serving_desc": "1 bowl with roasted peanuts & herbs (180g)",
        "calories": 240,
        "protein": 5.2,
        "carbs": 44.0,
        "fat": 5.5,
        "fiber": 3.2,
        "source": "Standardized Recipe Estimate based on ICMR-NIN Indian Food Composition Tables (IFCT 2017)",
    },
    "khichdi": {
        "canonical_name": "Moong Dal Khichdi",
        "aliases": ["khichdi", "moong dal khichdi", "dal khichdi", "khichuri"],
        "category": "Wholesome Rice & Lentil Mash",
        "serving_g": 250,
        "serving_desc": "1 medium bowl (approx 250g)",
        "calories": 280,
        "protein": 10.5,
        "carbs": 48.0,
        "fat": 5.2,
        "fiber": 5.5,
        "source": "Standardized Recipe Estimate based on ICMR-NIN Indian Food Composition Tables (IFCT 2017)",
    },
    "roti_chapati": {
        "canonical_name": "Whole Wheat Roti / Phulka",
        "aliases": ["roti", "chapati", "phulka", "whole wheat flatbread"],
        "category": "Unleavened Whole Grain Bread",
        "serving_g": 40,
        "serving_desc": "1 medium phulka / roti (~40g)",
        "calories": 105,
        "protein": 3.4,
        "carbs": 21.0,
        "fat": 0.8,
        "fiber": 2.8,
        "source": "ICMR-NIN Indian Food Composition Tables (IFCT 2017) [Code: Cereal Preparations]",
    },
    "naan": {
        "canonical_name": "Plain Tandoori Naan",
        "aliases": ["naan", "tandoori naan", "butter naan", "garlic naan"],
        "category": "Tandoor Baked Flatbread",
        "serving_g": 90,
        "serving_desc": "1 piece (~90g)",
        "calories": 260,
        "protein": 7.5,
        "carbs": 46.0,
        "fat": 5.0,
        "fiber": 2.0,
        "source": "USDA FoodData Central [FDC ID: 172900] & IFCT 2017",
    },
    "kathi_roll": {
        "canonical_name": "Paneer Kathi Roll",
        "aliases": ["kathi roll", "kathiroll", "frankie", "paneer roll", "veg roll"],
        "category": "Wrap / Flatbread Roll",
        "serving_g": 180,
        "serving_desc": "1 roll with spiced filling & onions (180g)",
        "calories": 360,
        "protein": 11.5,
        "carbs": 44.0,
        "fat": 15.0,
        "fiber": 4.0,
        "source": "Standardized Recipe Estimate based on ICMR-NIN Indian Food Composition Tables (IFCT 2017)",
    },
    "panipuri": {
        "canonical_name": "Pani Puri / Golgappa",
        "aliases": ["panipuri", "pani puri", "golgappa", "puchka"],
        "category": "Street Food / Filled Crisp Spheres",
        "serving_g": 150,
        "serving_desc": "6 puris with spiced mint water & potato-sprout filling",
        "calories": 170,
        "protein": 3.5,
        "carbs": 32.0,
        "fat": 3.5,
        "fiber": 2.8,
        "source": "Standardized Recipe Estimate based on ICMR-NIN Indian Food Composition Tables (IFCT 2017)",
    },
    "dabeli": {
        "canonical_name": "Kutchi Dabeli",
        "aliases": ["dabeli", "kutchi dabeli"],
        "category": "Street Food / Spiced Potato Bun",
        "serving_g": 140,
        "serving_desc": "1 piece with roasted peanuts & pomegranate (140g)",
        "calories": 280,
        "protein": 5.8,
        "carbs": 46.0,
        "fat": 8.5,
        "fiber": 3.8,
        "source": "Standardized Recipe Estimate based on ICMR-NIN Indian Food Composition Tables (IFCT 2017)",
    },
    "kofta": {
        "canonical_name": "Malai Kofta Curry",
        "aliases": ["kofta", "malai kofta", "veg kofta"],
        "category": "Paneer Dumplings in Rich Gravy",
        "serving_g": 220,
        "serving_desc": "1 bowl (~220g)",
        "calories": 390,
        "protein": 9.2,
        "carbs": 24.0,
        "fat": 29.0,
        "fiber": 3.2,
        "source": "Standardized Recipe Estimate based on ICMR-NIN Indian Food Composition Tables (IFCT 2017)",
    },

    # ── Universal Staples, Fresh Produce & Lean Proteins ──
    "apple": {
        "canonical_name": "Fresh Apple",
        "aliases": ["apple", "red apple", "green apple", "fresh apple"],
        "category": "Fresh Fruit",
        "serving_g": 180,
        "serving_desc": "1 medium apple (approx 180g)",
        "calories": 95,
        "protein": 0.5,
        "carbs": 25.0,
        "fat": 0.3,
        "fiber": 4.4,
        "source": "USDA FoodData Central [FDC ID: 171688]",
    },
    "banana": {
        "canonical_name": "Fresh Banana",
        "aliases": ["banana", "ripe banana", "yellow banana"],
        "category": "Fresh Fruit",
        "serving_g": 120,
        "serving_desc": "1 medium banana (approx 120g)",
        "calories": 105,
        "protein": 1.3,
        "carbs": 27.0,
        "fat": 0.3,
        "fiber": 3.1,
        "source": "USDA FoodData Central [FDC ID: 173944]",
    },
    "green_salad": {
        "canonical_name": "Mixed Green Salad",
        "aliases": ["green salad", "salad", "cucumber salad", "fresh salad", "garden salad"],
        "category": "Raw Vegetable Salad",
        "serving_g": 150,
        "serving_desc": "1 medium bowl (cucumber, tomato, lettuce, lemon)",
        "calories": 45,
        "protein": 2.0,
        "carbs": 9.0,
        "fat": 0.5,
        "fiber": 3.2,
        "source": "USDA FoodData Central [FDC ID: 169248]",
    },
    "boiled_egg": {
        "canonical_name": "Hard Boiled Egg",
        "aliases": ["boiled egg", "egg", "hard boiled egg", "eggs"],
        "category": "Poultry / Whole Egg",
        "serving_g": 50,
        "serving_desc": "1 large boiled egg (50g)",
        "calories": 78,
        "protein": 6.3,
        "carbs": 0.6,
        "fat": 5.3,
        "fiber": 0.0,
        "source": "USDA FoodData Central [FDC ID: 173424]",
    },
    "grilled_chicken": {
        "canonical_name": "Grilled Chicken Breast",
        "aliases": ["grilled chicken", "chicken breast", "roasted chicken", "chicken tikka"],
        "category": "Lean Poultry",
        "serving_g": 150,
        "serving_desc": "1 skinless grilled breast portion (150g)",
        "calories": 240,
        "protein": 44.0,
        "carbs": 0.0,
        "fat": 5.0,
        "fiber": 0.0,
        "source": "USDA FoodData Central [FDC ID: 171477]",
    },
    "steamed_rice": {
        "canonical_name": "Steamed White Basmati Rice",
        "aliases": ["white rice", "steamed rice", "cooked rice", "plain rice", "chawal"],
        "category": "Cooked Grain",
        "serving_g": 160,
        "serving_desc": "1 cup cooked (~160g)",
        "calories": 205,
        "protein": 4.2,
        "carbs": 45.0,
        "fat": 0.4,
        "fiber": 0.8,
        "source": "USDA FoodData Central [FDC ID: 169756] & IFCT 2017 [Code: A001]",
    },
    "curd_yogurt": {
        "canonical_name": "Plain Indian Curd / Dahi",
        "aliases": ["curd", "dahi", "yogurt", "plain curd", "greek yogurt"],
        "category": "Fermented Dairy",
        "serving_g": 150,
        "serving_desc": "1 small katori / cup (150g)",
        "calories": 98,
        "protein": 5.5,
        "carbs": 7.0,
        "fat": 5.2,
        "fiber": 0.0,
        "source": "ICMR-NIN Indian Food Composition Tables (IFCT 2017) [Code: Milk Products]",
    },
}


# ===============================================================================
# 2. Nutrition Matching and Scaling Helpers
# ===============================================================================

def _normalize_text(text: str) -> str:
    """Strips punctuation, lowercases, and compresses whitespace."""
    if not text:
        return ""
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
    return " ".join(cleaned.split())


def lookup_reference_food(food_name: str, food_items: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    """
    Looks up a recognized dish in the local reference database.
    Attempts:
      1. Direct key match
      2. Alias exact match
      3. Word-token intersection match
      4. Fallback search across recognized food components
    """
    if not food_name:
        return None

    normalized_name = _normalize_text(food_name)
    if not normalized_name:
        return None

    # 1 & 2: Direct key or alias exact match
    for key, item in NUTRITION_REFERENCE_DB.items():
        if normalized_name == key or normalized_name == _normalize_text(item["canonical_name"]):
            return item
        for alias in item.get("aliases", []):
            if normalized_name == _normalize_text(alias):
                return item

    # 3: Substring / token boundary match
    name_tokens = set(normalized_name.split())
    # Exclude trivial non-descriptive culinary words
    filler_words = {"homemade", "hot", "fresh", "delicious", "tasty", "spicy", "plate", "bowl", "of", "and", "with", "indian", "style", "traditional"}
    core_tokens = name_tokens - filler_words

    best_match = None
    best_overlap = 0

    for key, item in NUTRITION_REFERENCE_DB.items():
        for alias in item.get("aliases", []):
            alias_tokens = set(_normalize_text(alias).split()) - filler_words
            overlap = len(core_tokens & alias_tokens)
            if overlap > 0 and overlap >= len(alias_tokens) and overlap > best_overlap:
                best_overlap = overlap
                best_match = item

    if best_match:
        return best_match

    # 4: Search primary ingredients if dish name is a generic descriptor
    if food_items and isinstance(food_items, list):
        for ing in food_items:
            ing_norm = _normalize_text(str(ing))
            for key, item in NUTRITION_REFERENCE_DB.items():
                for alias in item.get("aliases", []):
                    if ing_norm == _normalize_text(alias):
                        return item

    return None


def parse_serving_weight_g(serving_text: Optional[str]) -> Optional[float]:
    """
    Extracts numerical gram weight from serving strings like 'approx 280g', 'portion: 350g', or '200g'.
    Avoids mistaking sub-ingredient weights in compound descriptions (e.g. '2 bhature + 200g chole') for total dish weight.
    """
    if not serving_text:
        return None

    text = serving_text.strip()

    # If it's a compound ingredient description with '+' or ' and ', check for explicit total indicator
    if '+' in text or ' and ' in text:
        total_match = re.search(r"(?:total|approx|overall|weight)[:\s~]*(\d+(?:\.\d+)?)\s*(?:g|gram|grams)\b", text, re.IGNORECASE)
        if total_match:
            try:
                val = float(total_match.group(1))
                if 40 <= val <= 1500:
                    return val
            except ValueError:
                pass
        return None

    # Matches patterns like '250g', '250 g', '250 grams', '250.5g'
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:g|gram|grams)\b", text, re.IGNORECASE)
    if match:
        try:
            val = float(match.group(1))
            if 30 <= val <= 1500:  # Plausible single-serving boundary
                return val
        except ValueError:
            pass

    return None


def scale_reference_nutrition(reference: Dict[str, Any], target_weight_g: float) -> Dict[str, Any]:
    """
    Scales standard reference values to a detected portion weight.
    Applies bounds (0.3x to 3.0x) to avoid unreasonable extrapolations.
    """
    base_weight = reference.get("serving_g", 100)
    if base_weight <= 0:
        base_weight = 100

    scale_ratio = target_weight_g / float(base_weight)
    clamped_ratio = max(0.3, min(3.0, scale_ratio))

    def _s(val: float) -> float:
        return round(val * clamped_ratio, 1)

    return {
        "calories": int(round(reference["calories"] * clamped_ratio)),
        "protein": _s(reference["protein"]),
        "carbs": _s(reference["carbs"]),
        "fat": _s(reference["fat"]),
        "fiber": _s(reference["fiber"]),
        "serving_g": int(round(target_weight_g)),
        "serving_desc": f"Adjusted portion (approx {int(round(target_weight_g))}g)",
        "scale_applied": round(clamped_ratio, 2),
    }


# ===============================================================================
# 3. Validation, Sanitization & Nutrition Integrity
# ===============================================================================

def sanitize_nutrient_value(val: Any, default: Optional[float] = None) -> Optional[float]:
    """Ensures nutrient is a non-negative, finite float."""
    if val is None:
        return default
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f) or f < 0:
            return default
        return round(f, 1)
    except (ValueError, TypeError):
        return default


def validate_and_balance_nutrition(nut_dict: Optional[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Validates nutrient values and checks thermodynamic plausibility.
    Uses the 4-4-9 Atwater factor system to cross-check energy density.
    Returns (cleaned_dict, status_str).
    """
    if not nut_dict or not isinstance(nut_dict, dict):
        return None, "insufficient_data"

    protein = sanitize_nutrient_value(nut_dict.get("protein"))
    carbs = sanitize_nutrient_value(nut_dict.get("carbs"))
    fat = sanitize_nutrient_value(nut_dict.get("fat"))
    fiber = sanitize_nutrient_value(nut_dict.get("fiber"), default=0.0)
    cals = sanitize_nutrient_value(nut_dict.get("calories"))

    # Need at least two core macronutrients or calories to form an estimate
    core_present = sum(1 for v in [protein, carbs, fat] if v is not None)
    if core_present < 2 and cals is None:
        return None, "insufficient_data"

    # Default missing macros to 0 if others are well defined
    p_val = protein if protein is not None else 0.0
    c_val = carbs if carbs is not None else 0.0
    f_val = fat if fat is not None else 0.0
    fib_val = fiber if fiber is not None else 0.0

    # Atwater macro energy check: 4 kcal/g protein, 4 kcal/g carbs, 9 kcal/g fat
    macro_cals = round((p_val * 4.0) + (c_val * 4.0) + (f_val * 9.0))

    if cals is None or cals <= 0:
        # Recompute from macronutrients
        cals_final = macro_cals
    elif abs(cals - macro_cals) > max(150, macro_cals * 0.5) and macro_cals > 50:
        # If model hallucinated wildly mismatched numbers (e.g. 50g fat but 30 kcal),
        # reconcile closer to the actual physical macro sum
        cals_final = int(round((cals + macro_cals) / 2))
    else:
        cals_final = int(round(cals))

    cleaned = {
        "calories": max(0, cals_final),
        "protein": p_val,
        "carbs": c_val,
        "fat": f_val,
        "fiber": fib_val,
        "serving": str(nut_dict.get("serving") or nut_dict.get("unit") or "1 standard serving"),
        "unit": str(nut_dict.get("unit") or "1 serving"),
        "tip": str(nut_dict.get("tip") or "").strip(),
    }
    return cleaned, "available"


# ===============================================================================
# 4. Transparent Health Scoring Logic (0-100 Scale)
# ===============================================================================

def compute_health_score(nut: Dict[str, Any]) -> Tuple[Optional[int], str, List[str]]:
    """
    Computes a transparent, deterministic single-serving nutritional health score (0-100).

    IMPORTANT: This is a single-serving nutritional balance heuristic based on
    macronutrient distribution and caloric density. It is NOT a clinical diagnosis
    or an evaluation of an individual's overall lifestyle or total daily diet.

    Scoring Framework:
      - Baseline: 60 points
      - Protein Adequacy: up to +15 pts (>=15g: +15, 8-14g: +10, 4-7g: +5, <4g in heavy meal: -5)
      - Dietary Fiber: up to +15 pts (>=7g: +15, 4-6g: +10, 2-3g: +5, <1g in heavy meal: -6)
      - Fat & Calorie Balance: up to +/- 20 pts
          * Calories from fat <= 35%: +10 pts
          * Calories from fat 36-48%: +2 pts
          * Calories from fat 49-60%: -8 pts
          * Calories from fat > 60%: -15 pts
          * Caloric load > 750 kcal: -10 pts
          * Balanced low-cal density (< 250 kcal with good fiber/protein): +5 pts
      - Clamped to integer [10, 100].

    Returns:
      (score, label, breakdown_factors)
    """
    cals = nut.get("calories")
    p = nut.get("protein")
    c = nut.get("carbs")
    f = nut.get("fat")
    fib = nut.get("fiber", 0.0)

    if any(v is None for v in [cals, p, c, f]):
        return None, "Insufficient Data", ["Incomplete macronutrient data for score computation"]

    cals = float(cals)
    p = float(p)
    c = float(c)
    f = float(f)
    fib = float(fib or 0.0)

    if cals <= 0:
        return None, "Insufficient Data", ["Zero or non-positive energy density"]

    score = 60.0
    breakdown = []

    # 1. Protein Adequacy
    if p >= 15.0:
        score += 15.0
        breakdown.append(f"+15 pts: High protein content ({p}g supports satiety & muscle maintenance)")
    elif p >= 8.0:
        score += 10.0
        breakdown.append(f"+10 pts: Moderate protein contribution ({p}g)")
    elif p >= 4.0:
        score += 5.0
        breakdown.append(f"+5 pts: Mild protein contribution ({p}g)")
    elif cals > 350:
        score -= 5.0
        breakdown.append(f"-5 pts: Relatively low protein ({p}g) relative to meal energy ({int(cals)} kcal)")

    # 2. Dietary Fiber Richness
    if fib >= 7.0:
        score += 15.0
        breakdown.append(f"+15 pts: High dietary fiber ({fib}g aids gut health & glucose regulation)")
    elif fib >= 4.0:
        score += 10.0
        breakdown.append(f"+10 pts: Good dietary fiber content ({fib}g)")
    elif fib >= 2.0:
        score += 5.0
        breakdown.append(f"+5 pts: Modest dietary fiber ({fib}g)")
    elif cals > 350:
        score -= 6.0
        breakdown.append(f"-6 pts: Low dietary fiber ({fib}g) in an energy-dense preparation")

    # 3. Lipid Ratio & Energy Density
    fat_cals = f * 9.0
    fat_pct = (fat_cals / cals) * 100.0 if cals > 0 else 0.0

    if fat_pct <= 35.0:
        score += 10.0
        breakdown.append(f"+10 pts: Favorable lipid distribution ({fat_pct:.1f}% calories from fat)")
    elif fat_pct <= 48.0:
        score += 2.0
        breakdown.append(f"+2 pts: Moderate fat density ({fat_pct:.1f}% calories from fat)")
    elif fat_pct <= 60.0:
        score -= 8.0
        breakdown.append(f"-8 pts: High fat concentration ({fat_pct:.1f}% calories from fat)")
    else:
        score -= 15.0
        breakdown.append(f"-15 pts: Very high lipid concentration ({fat_pct:.1f}% calories from fat, typical of deep frying)")

    if cals > 750:
        score -= 10.0
        breakdown.append(f"-10 pts: High single-serving caloric load ({int(cals)} kcal)")
    elif cals <= 250 and (p >= 5.0 or fib >= 3.0):
        score += 5.0
        breakdown.append("+5 pts: Nutrient-dense, light energy profile")

    # Bounded range [10, 100]
    final_score = int(round(max(10.0, min(100.0, score))))

    # Deterministic categorical label
    if final_score >= 80:
        label = "Nutrient-Dense & Well-Balanced"
    elif final_score >= 65:
        label = "Balanced Meal"
    elif final_score >= 50:
        label = "Moderate / Energy-Dense"
    else:
        label = "Indulgent / Calorie-Dense"

    return final_score, label, breakdown


# ===============================================================================
# 5. Dietary Insights & Pairing Suggestions
# ===============================================================================

def generate_dietary_insights(nut: Dict[str, Any]) -> List[str]:
    """
    Generates deterministic, respectful, and culturally appropriate nutritional insights.
    Does NOT offer medical diagnoses or disease-treatment claims.
    """
    insights: List[str] = []
    cals = float(nut.get("calories", 0))
    p = float(nut.get("protein", 0))
    c = float(nut.get("carbs", 0))
    f = float(nut.get("fat", 0))
    fib = float(nut.get("fiber", 0))

    # Caloric load guidance
    if cals >= 600:
        insights.append(
            f"Portion Awareness: At ~{int(cals)} kcal, this serving is energy-dense. Pairing with light or fresh vegetable sides provides good balance."
        )
    elif cals > 0 and cals <= 220:
        insights.append(
            f"Light Energy Profile: At ~{int(cals)} kcal, this makes an ideal light meal or snack that easily fits daily calorie targets."
        )

    # Protein insights
    if p >= 15.0:
        insights.append(
            f"Rich Protein Source: Provides {p}g of protein, contributing significantly toward muscle repair and satiety."
        )
    elif p < 7.0 and cals >= 250:
        insights.append(
            f"Protein Pairing Opportunity: With {p}g protein, pairing this with lentils (dal), sprouts, paneer, tofu, or yogurt (raita) can improve amino acid balance."
        )

    # Fiber insights
    if fib >= 6.0:
        insights.append(
            f"Fiber-Rich: Delivers {fib}g dietary fiber, which promotes digestive health and helps stabilize post-meal blood sugar."
        )
    elif fib < 2.5 and cals >= 250:
        insights.append(
            f"Fiber Boost Suggestion: Contains {fib}g fiber. Adding a side of sliced cucumber, carrots, or leafy greens will enhance dietary fiber."
        )

    # Lipid / Cooking method observations
    if cals > 0:
        fat_pct = (f * 9.0 / cals) * 100.0
        if fat_pct > 48.0:
            insights.append(
                f"Lipid Awareness: Fats account for ~{int(fat_pct)}% of calories (often from oil, ghee, or cream). Enjoy as a satisfying treat within a balanced day."
            )
        elif fat_pct <= 30.0 and p >= 8.0:
            insights.append("Macronutrient Equilibrium: Well-proportioned ratio of complex carbohydrates, lean protein, and moderate healthy fats.")

    if not insights:
        insights.append("Nutritionally well-rounded serving with standard culinary macronutrient proportions.")

    return insights


# ===============================================================================
# 6. Master Estimation Pipeline
# ===============================================================================

def estimate_nutrition_and_score(
    food_name: str,
    food_items: Optional[List[str]] = None,
    gemini_raw_nutrition: Optional[Dict[str, Any]] = None,
    is_food: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Executes the full Activity 2.2 pipeline:
      1. Non-food guard -> returns None.
      2. Checks local reference database (ICMR IFCT 2017 / USDA FDC).
      3. Applies portion scaling if weight is extracted.
      4. Falls back to sanitized AI visual estimation for unknown dishes.
      5. Calculates deterministic 0-100 health score with breakdown.
      6. Formulates practical dietary insights.
    """
    if not is_food:
        return None

    ref_match = lookup_reference_food(food_name, food_items)
    serving_str = ""
    if gemini_raw_nutrition and isinstance(gemini_raw_nutrition, dict):
        serving_str = str(gemini_raw_nutrition.get("serving") or "")

    detected_weight_g = parse_serving_weight_g(serving_str)

    if ref_match:
        # Reference-matched dish
        if detected_weight_g and abs(detected_weight_g - ref_match["serving_g"]) > 30:
            # Portion adjusted
            scaled = scale_reference_nutrition(ref_match, detected_weight_g)
            method = "reference_portion_scaled"
            data_source = f"{ref_match['source']} (Portion scaled to {scaled['serving_g']}g)"
            serving_label = scaled["serving_desc"]
            cals = scaled["calories"]
            p = scaled["protein"]
            c = scaled["carbs"]
            f = scaled["fat"]
            fib = scaled["fiber"]
            unc_note = (
                f"Reference values from {ref_match['canonical_name']} scaled to visible portion ({scaled['serving_g']}g). "
                "Actual energy depends on culinary preparation, oil type, and sodium usage."
            )
        else:
            # Standard reference portion
            method = "reference_standard"
            data_source = ref_match["source"]
            serving_label = ref_match["serving_desc"]
            cals = ref_match["calories"]
            p = ref_match["protein"]
            c = ref_match["carbs"]
            f = ref_match["fat"]
            fib = ref_match["fiber"]
            unc_note = (
                "Values derived from verified food composition reference tables for standard culinary recipe. "
                "Commercial restaurant preparations may vary in cooking fats."
            )

        core_nut = {
            "calories": cals,
            "protein": p,
            "carbs": c,
            "fat": f,
            "fiber": fib,
            "serving": serving_label,
            "unit": "1 serving",
            "tip": (gemini_raw_nutrition.get("tip") if gemini_raw_nutrition else "") or "Reference standard profile"
        }
    else:
        # Unknown / custom mixed dish -> Sanitized AI visual estimation
        core_nut, status = validate_and_balance_nutrition(gemini_raw_nutrition)
        if not core_nut:
            # Insufficient data
            return {
                "status": "insufficient_data",
                "message": "Nutritional reference unavailable and visual estimation was insufficient.",
                "calories": None,
                "protein": None,
                "carbs": None,
                "fat": None,
                "fiber": None,
                "serving": serving_str or "Unknown portion",
                "unit": "1 serving",
                "health_score": None,
                "health_score_label": "Insufficient Data",
                "health_score_breakdown": ["Unable to determine nutritional values with confidence."],
                "data_source": "Unavailable",
                "estimation_method": "insufficient_data",
                "uncertainty_note": "Visual analysis could not resolve reliable macronutrient data for this food.",
                "insights": ["Nutritional values could not be estimated with sufficient confidence."],
                "tip": ""
            }

        method = "ai_visual_estimation"
        data_source = "Gemini Multimodal AI Culinary Heuristics (Approximate)"
        unc_note = (
            "Provisional AI visual estimation based on visible ingredients and standard recipe proportions. "
            "Not a laboratory measurement; portion sizes and hidden fats are approximate."
        )

    # Health Scoring
    score, score_label, score_breakdown = compute_health_score(core_nut)

    # Dietary Insights
    insights = generate_dietary_insights(core_nut)

    # Consolidated Output Contract
    return {
        "status": "available",
        "calories": core_nut["calories"],
        "protein": core_nut["protein"],
        "carbs": core_nut["carbs"],
        "fat": core_nut["fat"],
        "fiber": core_nut["fiber"],
        "serving": core_nut["serving"],
        "unit": core_nut["unit"],
        "health_score": score,
        "health_score_label": score_label,
        "health_score_breakdown": score_breakdown,
        "data_source": data_source,
        "estimation_method": method,
        "uncertainty_note": unc_note,
        "insights": insights,
        "tip": core_nut.get("tip") or insights[0]
    }
