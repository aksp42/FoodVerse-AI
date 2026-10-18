"""
FoodVerse AI — User Profile, Goal, and Preference Processing Service
Smart Bridge Milestone 5, Activity 5.1

Responsibilities:
  1. Validate profile fields: Age (1–120), Height (50–250 cm), Weight (20–300 kg).
  2. Validate and normalize dietary preferences (Vegetarian, Vegan, Non-Vegetarian, Eggetarian, Jain, Pescatarian, Keto, etc.).
  3. Validate and normalize health goals (Weight Loss, Weight Maintain, Muscle Gain, Heart Healthy, Diabetic Friendly, etc.).
  4. Explicitly separate Allergies (strict safety exclusion) from Dislikes (preference exclusion)
     and Food Intolerances (e.g. lactose, gluten intolerance).
  5. Calculate estimated daily calorie and macro guidelines (Mifflin-St Jeor formula baseline)
     while clearly stating they are educational estimates, not medical advice or clinical prescriptions.
  6. Filter ingredient recommendations: strictly block any ingredient matching an allergy or intolerance.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Constants & Allowed Enums
# ---------------------------------------------------------------------------

VALID_DIETS: Set[str] = {
    "vegetarian",
    "vegan",
    "non-vegetarian",
    "eggetarian",
    "jain",
    "pescatarian",
    "keto",
    "halal",
    "kosher",
    "any",
}

VALID_GOALS: Set[str] = {
    "weight loss",
    "weight maintain",
    "muscle gain",
    "heart healthy",
    "diabetic friendly",
    "general wellness",
    "balanced eating",
}

VALID_ACTIVITY_LEVELS: Set[str] = {
    "sedentary",
    "lightly active",
    "moderately active",
    "very active",
    "extra active",
}

ACTIVITY_MULTIPLIERS: Dict[str, float] = {
    "sedentary": 1.2,
    "lightly active": 1.375,
    "moderately active": 1.55,
    "very active": 1.725,
    "extra active": 1.9,
}

GOAL_CALORIE_ADJUSTMENTS: Dict[str, int] = {
    "weight loss": -400,
    "weight maintain": 0,
    "muscle gain": +350,
    "heart healthy": -150,
    "diabetic friendly": -200,
    "general wellness": 0,
    "balanced eating": 0,
}


# ---------------------------------------------------------------------------
# Validation & Normalization
# ---------------------------------------------------------------------------

def normalize_list_items(raw: Any) -> List[str]:
    """Converts a comma-separated string or list of items into a clean list of lowercased strings."""
    if not raw:
        return []
    if isinstance(raw, str):
        items = re.split(r'[,;|\n]+', raw)
    elif isinstance(raw, list):
        items = [str(x) for x in raw]
    else:
        return []
    
    cleaned = []
    for item in items:
        s = item.strip().lower()
        if s and s not in cleaned:
            cleaned.append(s)
    return cleaned


def validate_and_normalize_profile(raw_data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validates and normalizes raw user profile inputs.
    Returns (normalized_profile, validation_errors_list).
    """
    errors: List[str] = []
    
    if not isinstance(raw_data, dict):
        return {}, ["Profile data must be a JSON object."]

    # 1. Demographics & Metrics (Optional or Required if provided)
    age = raw_data.get("age")
    if age is not None and age != "":
        try:
            age = int(age)
            if not (1 <= age <= 120):
                errors.append("Age must be between 1 and 120 years.")
        except (ValueError, TypeError):
            errors.append("Age must be a valid integer.")
            age = None
    else:
        age = None

    height_cm = raw_data.get("height_cm")
    if height_cm is not None and height_cm != "":
        try:
            height_cm = float(height_cm)
            if not (50.0 <= height_cm <= 250.0):
                errors.append("Height must be between 50 and 250 cm.")
        except (ValueError, TypeError):
            errors.append("Height must be a valid numeric measurement in cm.")
            height_cm = None
    else:
        height_cm = None

    weight_kg = raw_data.get("weight_kg")
    if weight_kg is not None and weight_kg != "":
        try:
            weight_kg = float(weight_kg)
            if not (20.0 <= weight_kg <= 300.0):
                errors.append("Weight must be between 20 and 300 kg.")
        except (ValueError, TypeError):
            errors.append("Weight must be a valid numeric measurement in kg.")
            weight_kg = None
    else:
        weight_kg = None

    gender = str(raw_data.get("gender") or "unspecified").strip().lower()
    if gender not in {"male", "female", "other", "unspecified"}:
        gender = "unspecified"

    # 2. Dietary Preference
    raw_diet = str(raw_data.get("diet") or "Vegetarian").strip()
    diet_key = raw_diet.lower()
    if diet_key not in VALID_DIETS:
        errors.append(f"Invalid dietary preference '{raw_diet}'. Valid options: {', '.join(sorted(d.title() for d in VALID_DIETS))}.")
        diet_norm = "Vegetarian"
    else:
        diet_norm = raw_diet.title() if raw_diet.lower() != "jain" else "Jain"

    # 3. Health Goal
    raw_goal = str(raw_data.get("goal") or "Weight Maintain").strip()
    goal_key = raw_goal.lower()
    if goal_key not in VALID_GOALS:
        errors.append(f"Invalid health goal '{raw_goal}'. Valid options: {', '.join(sorted(g.title() for g in VALID_GOALS))}.")
        goal_norm = "Weight Maintain"
    else:
        goal_norm = raw_goal.title()

    # 4. Activity Level
    raw_activity = str(raw_data.get("activity_level") or "moderately active").strip()
    activity_key = raw_activity.lower()
    if activity_key not in VALID_ACTIVITY_LEVELS:
        activity_norm = "moderately active"
    else:
        activity_norm = activity_key

    # 5. Distinct Classification: Allergies vs Intolerances vs Dislikes vs Restrictions
    allergies = normalize_list_items(raw_data.get("allergies"))
    intolerances = normalize_list_items(raw_data.get("intolerances"))
    dislikes = normalize_list_items(raw_data.get("dislikes"))
    restrictions = normalize_list_items(raw_data.get("restrictions"))

    # 6. Contact & metadata
    name = str(raw_data.get("name") or "").strip()
    phone = str(raw_data.get("phone") or "").strip()
    budget = str(raw_data.get("budget") or "Medium").strip().title()
    if budget not in {"Low", "Medium", "High"}:
        budget = "Medium"

    # 7. Estimated daily calorie target calculation (Educational Guideline only)
    estimated_calories, bmr = calculate_estimated_calorie_target(
        age=age,
        height_cm=height_cm,
        weight_kg=weight_kg,
        gender=gender,
        activity_level=activity_norm,
        goal=goal_norm,
    )

    normalized_profile = {
        "name": name,
        "phone": phone,
        "age": age,
        "gender": gender,
        "height_cm": height_cm,
        "weight_kg": weight_kg,
        "diet": diet_norm,
        "goal": goal_norm,
        "activity_level": activity_norm,
        "budget": budget,
        "allergies": allergies,
        "intolerances": intolerances,
        "dislikes": dislikes,
        "restrictions": restrictions,
        "calorie_target": estimated_calories,
        "bmr": bmr,
        "medical_disclaimer": (
            "Calorie targets and dietary recommendations are algorithmic estimates for educational "
            "and general wellness planning only. They do not constitute clinical diagnosis, medical advice, "
            "or therapeutic nutritional prescription."
        ),
    }

    return normalized_profile, errors


def calculate_estimated_calorie_target(
    age: Optional[int],
    height_cm: Optional[float],
    weight_kg: Optional[float],
    gender: str,
    activity_level: str,
    goal: str,
) -> Tuple[int, Optional[int]]:
    """
    Computes an estimated daily calorie intake based on the Mifflin-St Jeor equation.
    If biometric data is incomplete, falls back to standard goal-based reference guidelines.
    """
    default_goal_targets = {
        "Weight Loss": 1500,
        "Weight Maintain": 1900,
        "Muscle Gain": 2400,
        "Heart Healthy": 1800,
        "Diabetic Friendly": 1700,
        "General Wellness": 1900,
        "Balanced Eating": 1900,
    }

    if age is None or height_cm is None or weight_kg is None:
        return default_goal_targets.get(goal, 1900), None

    # Mifflin-St Jeor formula
    # BMR = 10*weight(kg) + 6.25*height(cm) - 5*age(y) + s
    # s = +5 for male, -161 for female, -78 for other/unspecified
    if gender == "male":
        s = 5
    elif gender == "female":
        s = -161
    else:
        s = -78

    bmr = round(10.0 * weight_kg + 6.25 * height_cm - 5.0 * age + s)
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.375)
    tdee = bmr * multiplier

    adj = GOAL_CALORIE_ADJUSTMENTS.get(goal.lower(), 0)
    target = max(1200, min(3800, round(tdee + adj)))
    return target, bmr


# ---------------------------------------------------------------------------
# Strict Safety Filter for Recipes & Meal Plans
# ---------------------------------------------------------------------------

def is_ingredient_safe_for_user(ingredient_name: str, profile: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Checks if an ingredient is strictly safe given the user's allergies,
    intolerances, and dietary restrictions.
    Returns (is_safe: bool, reason: str | None).
    """
    ing_lower = ingredient_name.lower().strip()
    
    # 1. Check Allergies (Strict Safety Stop)
    for allergy in profile.get("allergies", []):
        if not allergy:
            continue
        allergy_clean = allergy.lower().strip()
        if allergy_clean in ing_lower or ing_lower in allergy_clean:
            return False, f"Conflicts with declared allergen: '{allergy}'"
        
        # Check standard allergen synonym mappings
        if "shellfish" in allergy_clean:
            shellfish_terms = {"shrimp", "prawn", "crab", "lobster", "clam", "oyster", "mussel", "scallop", "squid", "octopus"}
            if any(term in ing_lower for term in shellfish_terms):
                return False, f"Conflicts with declared allergen: '{allergy}'"
        elif "tree nut" in allergy_clean or "tree nuts" in allergy_clean or allergy_clean == "nuts" or allergy_clean == "nut":
            tree_nut_terms = {"almond", "cashew", "walnut", "pistachio", "pecan", "hazelnut", "macadamia", "brazil nut"}
            if any(term in ing_lower for term in tree_nut_terms):
                return False, f"Conflicts with declared allergen: '{allergy}'"
        elif "peanut" in allergy_clean:
            if "peanut" in ing_lower or "groundnut" in ing_lower:
                return False, f"Conflicts with declared allergen: '{allergy}'"
        elif "egg" in allergy_clean:
            egg_terms = {"egg", "mayo", "mayonnaise", "albumen"}
            if any(term in ing_lower for term in egg_terms):
                return False, f"Conflicts with declared allergen: '{allergy}'"
        elif "fish" in allergy_clean:
            fish_terms = {"salmon", "tuna", "cod", "tilapia", "trout", "mackerel", "anchovy", "fish", "sardine"}
            if any(term in ing_lower for term in fish_terms):
                return False, f"Conflicts with declared allergen: '{allergy}'"
        elif "soy" in allergy_clean:
            soy_terms = {"soy", "soya", "tofu", "tempeh", "edamame", "miso"}
            if any(term in ing_lower for term in soy_terms):
                return False, f"Conflicts with declared allergen: '{allergy}'"

    # 2. Check Intolerances (e.g. lactose, gluten)
    for intolerance in profile.get("intolerances", []):
        if intolerance:
            # Handle common intolerance synonyms
            if "lactose" in intolerance or "milk" in intolerance or "dairy" in intolerance:
                dairy_terms = {"milk", "paneer", "cheese", "cream", "butter", "curd", "yogurt", "ghee", "dairy"}
                if any(d in ing_lower for d in dairy_terms):
                    return False, f"Conflicts with declared intolerance: '{intolerance}'"
            elif "gluten" in intolerance:
                gluten_terms = {"wheat", "flour", "atta", "maida", "bread", "barley", "rye", "gluten"}
                if any(g in ing_lower for g in gluten_terms):
                    return False, f"Conflicts with declared intolerance: '{intolerance}'"
            elif intolerance in ing_lower or ing_lower in intolerance:
                return False, f"Conflicts with declared intolerance: '{intolerance}'"

    # 3. Check Prohibited Restrictions
    for res in profile.get("restrictions", []):
        if res and (res in ing_lower or ing_lower in res):
            return False, f"Conflicts with dietary restriction: '{res}'"

    return True, None
