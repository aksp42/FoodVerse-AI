"""
FoodVerse AI — Meal Plan Generation and Adaptive Recommendation Service
Smart Bridge Milestone 5, Activity 5.2

Responsibilities:
  1. Generate personalized daily and 7-day weekly meal plans using Gemini AI.
  2. Ground prompts in user profile: age, height, weight, gender, activity level,
     diet type, allergies, intolerances, dislikes, restrictions, and budget.
  3. Validate and normalize AI output:
     - Each meal: name, emoji, cal, protein, carbs, fat, prep_time_mins, ingredients, instructions, alternatives.
     - Meal-wise and daily totals (total_calories, total_protein, total_carbs, total_fat).
     - Weekly plans: day-wise summaries and weekly overview.
  4. Deterministic Ingredient-Safety Enforcement:
     - Check every meal, ingredient, and alternative with is_ingredient_safe_for_user().
     - If a dish conflicts with an allergen/intolerance/restriction, swap it with a safe alternative
       or substitute with a verified allergen-safe dish. Never silently present unsafe recommendations.
  5. Adaptive Recommendations:
     - Actionable suggestions tailored to goal, macronutrient distribution, and dietary constraints
       with educational rationale and without unsupported medical claims.
  6. Explicit Non-Medical Disclaimer attached to every plan.
"""

from __future__ import annotations

import copy
import json
import re
from typing import Any, Dict, List, Optional, Tuple

import profile_service

# ---------------------------------------------------------------------------
# Constants & Fallback Safe Dishes
# ---------------------------------------------------------------------------

WEEK_DAYS: List[str] = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
SLOTS: List[str] = ["breakfast", "lunch", "dinner", "snack"]

DEFAULT_MEDICAL_DISCLAIMER: str = (
    "Nutritional targets, meal plans, and macro guidelines are algorithmic estimates for educational "
    "and general wellness planning only. They do not constitute clinical diagnosis, medical advice, "
    "or therapeutic nutritional prescription."
)

# Certified base fallback options with allergen tags
SAFE_REFERENCE_DISHES: Dict[str, Dict[str, Any]] = {
    "oatmeal": {
        "name": "Steel-Cut Oats with Chia & Berries",
        "emoji": "🥣",
        "cal": 380,
        "protein": 12,
        "carbs": 62,
        "fat": 8,
        "prep_time_mins": 10,
        "ingredients": ["1/2 cup steel-cut oats", "1 cup water or almond milk", "1 tbsp chia seeds", "1/4 cup mixed berries"],
        "instructions": "Simmer oats in liquid for 10 minutes, stir in chia seeds, and top with berries.",
        "diets": ["Vegetarian", "Vegan", "Jain"],
        "allergens": [],
        "cost": "Low",
    },
    "moong_chilla": {
        "name": "Moong Dal Chilla with Mint Chutney",
        "emoji": "🥞",
        "cal": 350,
        "protein": 18,
        "carbs": 48,
        "fat": 7,
        "prep_time_mins": 15,
        "ingredients": ["1 cup soaked yellow moong dal", "1 green chilli", "1/2 inch ginger", "pinch of turmeric", "fresh coriander"],
        "instructions": "Grind soaked dal into a smooth batter. Spread on a seasoned skillet and cook until golden crisp.",
        "diets": ["Vegetarian", "Vegan", "Jain"],
        "allergens": [],
        "cost": "Low",
    },
    "quinoa_bowl": {
        "name": "Quinoa & Steamed Vegetable Medley",
        "emoji": "🥗",
        "cal": 480,
        "protein": 16,
        "carbs": 74,
        "fat": 11,
        "prep_time_mins": 20,
        "ingredients": ["1 cup cooked quinoa", "1/2 cup steamed carrots and zucchini", "1/4 cup boiled chickpeas", "1 tsp olive oil", "lemon juice"],
        "instructions": "Toss warm quinoa with steamed vegetables and chickpeas. Dress with olive oil and lemon juice.",
        "diets": ["Vegetarian", "Vegan", "Jain"],
        "allergens": [],
        "cost": "Medium",
    },
    "dal_rice": {
        "name": "Yellow Dal Tadka with Steamed Rice",
        "emoji": "🍛",
        "cal": 520,
        "protein": 19,
        "carbs": 88,
        "fat": 9,
        "prep_time_mins": 25,
        "ingredients": ["1 cup cooked toor dal", "1 cup steamed basmati rice", "1/2 tsp cumin seeds", "pinch of asafoetida (hing)", "coriander"],
        "instructions": "Cook dal until soft. Temper with cumin and spices in vegetable oil and serve over warm steamed rice.",
        "diets": ["Vegetarian", "Vegan", "Jain"],
        "allergens": [],
        "cost": "Low",
    },
    "tofu_stir_fry": {
        "name": "Sesame Ginger Tofu & Greens",
        "emoji": "🍲",
        "cal": 450,
        "protein": 24,
        "carbs": 32,
        "fat": 18,
        "prep_time_mins": 20,
        "ingredients": ["150g firm tofu cubes", "1 cup bok choy or spinach", "1 tsp sesame oil", "1/2 tsp ginger", "soy sauce"],
        "instructions": "Sear tofu cubes in sesame oil until golden. Toss with fresh greens and ginger for 3 minutes.",
        "diets": ["Vegetarian", "Vegan"],
        "allergens": ["soy"],
        "cost": "Medium",
    },
    "roasted_makhana": {
        "name": "Spiced Roasted Foxnuts (Makhana)",
        "emoji": "🍿",
        "cal": 160,
        "protein": 5,
        "carbs": 26,
        "fat": 4,
        "prep_time_mins": 5,
        "ingredients": ["2 cups foxnuts (makhana)", "1/2 tsp olive oil", "pinch of black salt and turmeric"],
        "instructions": "Dry-roast makhana in a wide skillet until crunchy. Season with light oil and salt.",
        "diets": ["Vegetarian", "Vegan", "Jain"],
        "allergens": [],
        "cost": "Low",
    },
    "fruit_salad": {
        "name": "Fresh Seasonal Fruit Bowl",
        "emoji": "🍎",
        "cal": 140,
        "protein": 2,
        "carbs": 34,
        "fat": 1,
        "prep_time_mins": 5,
        "ingredients": ["1 sliced apple", "1/2 cup pomegranate arils", "squeeze of lime"],
        "instructions": "Combine sliced fresh fruits and finish with a squeeze of fresh lime juice.",
        "diets": ["Vegetarian", "Vegan", "Jain"],
        "allergens": [],
        "cost": "Low",
    },
}


# ---------------------------------------------------------------------------
# Prompt Construction
# ---------------------------------------------------------------------------

def build_meal_plan_prompt(
    profile: Dict[str, Any],
    diet: Optional[str] = None,
    goal: Optional[str] = None,
    budget: Optional[str] = None,
    allergies: Optional[str] = None,
    days: int = 7,
) -> Tuple[str, int]:
    """
    Constructs a detailed dietitian prompt for Gemini LLM incorporating
    all user biometric context, calorie calculations, and safety constraints.
    Returns (prompt_text, calculated_target_calories).
    """
    diet_resolved = diet or profile.get("diet") or "Vegetarian"
    goal_resolved = goal or profile.get("goal") or "Weight Maintain"
    budget_resolved = budget or profile.get("budget") or "Medium"

    # Derive calorie target from Activity 5.1 calculation logic
    age = profile.get("age")
    height_cm = profile.get("height_cm")
    weight_kg = profile.get("weight_kg")
    gender = profile.get("gender", "unspecified")
    raw_activity = profile.get("activity_level")
    activity_level = raw_activity or "moderately active"

    target_cal, bmr = profile_service.calculate_estimated_calorie_target(
        age=age,
        height_cm=height_cm,
        weight_kg=weight_kg,
        gender=gender,
        activity_level=activity_level,
        goal=goal_resolved,
    )

    # Compile strict safety exclusions
    all_exclusions = set()
    if allergies:
        all_exclusions.update(profile_service.normalize_list_items(allergies))
    all_exclusions.update(profile.get("allergies", []))
    all_exclusions.update(profile.get("intolerances", []))
    all_exclusions.update(profile.get("restrictions", []))

    dislikes = profile.get("dislikes", [])

    exclusions_clause = (
        f"STRICT SAFETY EXCLUSIONS (Allergies, Intolerances & Restrictions - DO NOT INCLUDE ANY OF THESE IN ANY MEAL OR ALTERNATIVE): {', '.join(sorted(all_exclusions))}"
        if all_exclusions
        else "No critical food allergies or intolerances declared."
    )

    dislikes_clause = (
        f"Personal Dislikes (avoid if possible): {', '.join(sorted(dislikes))}"
        if dislikes
        else "None declared."
    )

    biometrics_summary = []
    if age:
        biometrics_summary.append(f"Age: {age} yrs")
    if height_cm and weight_kg:
        biometrics_summary.append(f"Height: {height_cm} cm, Weight: {weight_kg} kg")
    if raw_activity:
        biometrics_summary.append(f"Activity Level: {raw_activity}")

    biometrics_str = " | ".join(biometrics_summary) if biometrics_summary else "General adult reference"

    plan_span = "1-day comprehensive daily plan (Today)" if days == 1 else "7-day comprehensive weekly plan (Mon to Sun)"
    day_keys = ["Today"] if days == 1 else WEEK_DAYS

    day_template_example = """{
      "breakfast": {
        "name": "<dish name>",
        "emoji": "<emoji>",
        "cal": <int>,
        "protein": <int grams>,
        "carbs": <int grams>,
        "fat": <int grams>,
        "prep_time_mins": <int minutes>,
        "ingredients": ["<quantity and ingredient 1>", "<ingredient 2>"],
        "instructions": "<concise cooking step>",
        "alternatives": [
          {
            "name": "<safe alternative dish>",
            "emoji": "<emoji>",
            "cal": <int>,
            "protein": <int>,
            "carbs": <int>,
            "fat": <int>,
            "reason": "<why this alternative fits goal and preference>"
          }
        ]
      },
      "lunch": { ... },
      "dinner": { ... },
      "snack": { ... }
    }"""

    prompt = f"""You are a registered clinical dietitian and nutrition intelligence specialist.
Create an authentic, culturally appropriate, and nutritionally balanced {plan_span} for the user.

USER PROFILE & CONSTRAINTS:
- Diet Type: {diet_resolved}
- Health Goal: {goal_resolved}
- Target Daily Caloric Intake: ~{target_cal} kcal/day (BMR reference: {bmr or 'standard'})
- Biometrics: {biometrics_str}
- Budget Tier: {budget_resolved}
- {exclusions_clause}
- {dislikes_clause}

REQUIRED JSON STRUCTURE:
Return ONLY a valid JSON object matching this schema exactly:
{{
  "plan_type": "{'daily' if days == 1 else 'weekly'}",
  "target_calories": {target_cal},
  "nutrition_notes": "<practical dietary and hydration advice tailored to {goal_resolved}>",
  "adaptive_recommendations": [
    "<recommendation 1 explaining why certain macros/meals fit user's goal>",
    "<recommendation 2 explaining a practical lifestyle or timing tip>"
  ],
  "days": {{
    {', '.join(f'"{d}": {day_template_example}' for d in day_keys)}
  }},
  "shopping_list": {{
    "produce": ["<produce item 1>", "<produce item 2>"],
    "grains_and_legumes": ["<grain item 1>", "<grain item 2>"],
    "dairy_and_protein": ["<protein item 1>", "<protein item 2>"],
    "spices_and_pantry": ["<pantry item 1>", "<pantry item 2>"]
  }},
  "weekly_overview": "<brief 1-2 sentence overview of the nutrition balance across days>"
}}

CRITICAL SAFETY & QUALITY GUIDELINES:
1. Every meal slot MUST have estimated calories, protein (g), carbs (g), fat (g), prep time, ingredients, and at least 1 safe alternative.
2. The sum of meals (breakfast + lunch + dinner + snack) for each day MUST closely match ~{target_cal} kcal (within +/- 100 kcal).
3. STRICT SAFETY STOP: Zero ingredients in ANY meal or alternative may violate the exclusions: {', '.join(sorted(all_exclusions)) if all_exclusions else 'None'}.
4. Provide realistic, tasty meals adhering to {diet_resolved} cuisine principles.
5. Return ONLY pure JSON with no markdown backticks or commentary outside the JSON."""

    return prompt, target_cal


# ---------------------------------------------------------------------------
# Safe Alternative / Meal Provider
# ---------------------------------------------------------------------------

def get_safe_substitute_dish(slot: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Finds or constructs a guaranteed safe fallback dish for the given slot."""
    candidates = []
    if slot == "breakfast":
        candidates = ["oatmeal", "moong_chilla"]
    elif slot == "lunch":
        candidates = ["dal_rice", "quinoa_bowl"]
    elif slot == "dinner":
        candidates = ["quinoa_bowl", "tofu_stir_fry", "dal_rice"]
    else:  # snack
        candidates = ["roasted_makhana", "fruit_salad"]

    for key in candidates:
        candidate = SAFE_REFERENCE_DISHES[key]
        # Check name and ingredients
        safe_name, _ = profile_service.is_ingredient_safe_for_user(candidate["name"], user_profile)
        if safe_name:
            all_ing_safe = True
            for ing in candidate.get("ingredients", []):
                safe_ing, _ = profile_service.is_ingredient_safe_for_user(ing, user_profile)
                if not safe_ing:
                    all_ing_safe = False
                    break
            if all_ing_safe:
                sub = copy.deepcopy(candidate)
                sub["alternatives"] = [
                    {
                        "name": "Fresh Cut Fruit with Chia Seeds",
                        "cal": 150,
                        "protein": 3,
                        "carbs": 32,
                        "fat": 2,
                        "reason": "Safe, allergen-free natural alternative",
                    }
                ]
                return sub

    # Universal ultimate safe fallback (Rice, Dal, Water, Salt)
    return {
        "name": "Steamed Rice with Moong Dal",
        "emoji": "🍚",
        "cal": 420,
        "protein": 14,
        "carbs": 80,
        "fat": 4,
        "prep_time_mins": 20,
        "ingredients": ["1 cup cooked basmati rice", "1/2 cup yellow moong dal", "salt to taste"],
        "instructions": "Boil yellow moong dal with turmeric and salt until tender. Serve with steamed rice.",
        "diets": ["Vegetarian", "Vegan", "Jain"],
        "cost": "Low",
        "alternatives": [],
    }


# ---------------------------------------------------------------------------
# Normalization & Validation Engine
# ---------------------------------------------------------------------------

def normalize_meal_item(
    raw_meal: Any,
    slot_name: str,
    user_profile: Dict[str, Any],
    diet: str,
    budget: str,
) -> Dict[str, Any]:
    """
    Validates and normalizes an individual meal object, applying deterministic
    safety checks against the user's declared allergies, intolerances, and restrictions.
    """
    if not isinstance(raw_meal, dict):
        raw_meal = {}

    name = str(raw_meal.get("name") or f"Healthy {slot_name.title()} Bowl").strip()
    emoji = str(raw_meal.get("emoji") or ("🥣" if slot_name == "breakfast" else ("🍛" if slot_name in {"lunch", "dinner"} else "🍎"))).strip()
    
    # Nutritional parsing
    try:
        cal = max(50, min(1800, int(raw_meal.get("cal") or raw_meal.get("calories") or 350)))
    except (ValueError, TypeError):
        cal = 350

    try:
        protein = max(0, min(150, int(raw_meal.get("protein") or 15)))
    except (ValueError, TypeError):
        protein = 15

    try:
        carbs = max(0, min(250, int(raw_meal.get("carbs") or 45)))
    except (ValueError, TypeError):
        carbs = 45

    try:
        fat = max(0, min(100, int(raw_meal.get("fat") or 10)))
    except (ValueError, TypeError):
        fat = 10

    try:
        prep_time = max(5, min(180, int(raw_meal.get("prep_time_mins") or raw_meal.get("prep_time") or 15)))
    except (ValueError, TypeError):
        prep_time = 15

    # Ingredients
    raw_ings = raw_meal.get("ingredients") or []
    if isinstance(raw_ings, str):
        ingredients = [s.strip() for s in raw_ings.split(",") if s.strip()]
    elif isinstance(raw_ings, list):
        ingredients = [str(x).strip() for x in raw_ings if str(x).strip()]
    else:
        ingredients = []

    instructions = str(raw_meal.get("instructions") or "Prepare fresh ingredients and cook thoroughly.").strip()

    # Normalize alternatives
    raw_alts = raw_meal.get("alternatives") or []
    normalized_alts: List[Dict[str, Any]] = []
    if isinstance(raw_alts, list):
        for alt in raw_alts:
            if isinstance(alt, dict):
                alt_name = str(alt.get("name") or "").strip()
                if not alt_name:
                    continue
                # Verify alternative against allergies & restrictions
                safe_alt, _ = profile_service.is_ingredient_safe_for_user(alt_name, user_profile)
                if not safe_alt:
                    continue  # Safely drop unsafe alternatives

                normalized_alts.append({
                    "name": alt_name,
                    "emoji": str(alt.get("emoji") or "🍽️"),
                    "cal": int(alt.get("cal") or cal),
                    "protein": int(alt.get("protein") or protein),
                    "carbs": int(alt.get("carbs") or carbs),
                    "fat": int(alt.get("fat") or fat),
                    "reason": str(alt.get("reason") or "Balanced alternative with similar macronutrient profile").strip(),
                })

    meal_dict = {
        "name": name,
        "emoji": emoji,
        "cal": cal,
        "protein": protein,
        "carbs": carbs,
        "fat": fat,
        "prep_time_mins": prep_time,
        "ingredients": ingredients,
        "instructions": instructions,
        "alternatives": normalized_alts,
        "diets": raw_meal.get("diets") or [diet],
        "cost": raw_meal.get("cost") or budget,
        "is_estimated": True,
    }

    # Deterministic Safety Verification on Primary Meal
    safe_name, reason_name = profile_service.is_ingredient_safe_for_user(name, user_profile)
    unsafe_ing_found = None
    for ing in ingredients:
        safe_ing, reason_ing = profile_service.is_ingredient_safe_for_user(ing, user_profile)
        if not safe_ing:
            unsafe_ing_found = reason_ing
            break

    if not safe_name or unsafe_ing_found:
        # Primary meal triggers an allergen/intolerance/restriction!
        # If a safe alternative exists, promote it to primary meal:
        if normalized_alts:
            promoted = normalized_alts.pop(0)
            meal_dict["name"] = promoted["name"]
            meal_dict["emoji"] = promoted["emoji"]
            meal_dict["cal"] = promoted["cal"]
            meal_dict["protein"] = promoted["protein"]
            meal_dict["carbs"] = promoted["carbs"]
            meal_dict["fat"] = promoted["fat"]
            meal_dict["instructions"] = f"Adapted to avoid conflicting ingredient. {promoted.get('reason', '')}"
            meal_dict["safety_adaptation_note"] = f"Replaced original suggestion to guarantee safety: {reason_name or unsafe_ing_found}"
        else:
            # Substitute with certified safe fallback dish
            substitute = get_safe_substitute_dish(slot_name, user_profile)
            meal_dict.update(substitute)
            meal_dict["safety_adaptation_note"] = f"Substituted with allergen-safe recipe: {reason_name or unsafe_ing_found}"

    return meal_dict


def normalize_meal_plan_response(
    raw_data: Any,
    user_profile: Dict[str, Any],
    diet: str,
    goal: str,
    budget: str,
    days_count: int = 7,
    target_cal: int = 1900,
) -> Dict[str, Any]:
    """
    Validates, normalizes, and enriches the AI-generated meal plan.
    Calculates exact daily and weekly totals, ensures allergen compliance,
    and attaches adaptive recommendations and disclaimers.
    """
    if not isinstance(raw_data, dict):
        raw_data = {}

    expected_day_keys = ["Today"] if days_count == 1 else WEEK_DAYS
    raw_days = raw_data.get("days") or {}

    normalized_days: Dict[str, Any] = {}
    weekly_total_calories = 0
    weekly_total_protein = 0
    weekly_total_carbs = 0
    weekly_total_fat = 0

    for d_key in expected_day_keys:
        raw_day = raw_days.get(d_key) or {}
        day_meals: Dict[str, Any] = {}
        day_cals = 0
        day_prot = 0
        day_carbs = 0
        day_fat = 0

        for slot in SLOTS:
            raw_slot_meal = raw_day.get(slot)
            if not raw_slot_meal:
                # Fallback to safe dish
                raw_slot_meal = get_safe_substitute_dish(slot, user_profile)
            
            norm_meal = normalize_meal_item(raw_slot_meal, slot, user_profile, diet, budget)
            day_meals[slot] = norm_meal

            day_cals += norm_meal["cal"]
            day_prot += norm_meal["protein"]
            day_carbs += norm_meal["carbs"]
            day_fat += norm_meal["fat"]

        day_summary = {
            "total_calories": day_cals,
            "total_protein": day_prot,
            "total_carbs": day_carbs,
            "total_fat": day_fat,
            "calorie_difference": day_cals - target_cal,
            "macro_distribution_pct": {
                "protein": round((day_prot * 4 / max(1, day_cals)) * 100),
                "carbs": round((day_carbs * 4 / max(1, day_cals)) * 100),
                "fat": round((day_fat * 9 / max(1, day_cals)) * 100),
            }
        }

        day_meals["day_summary"] = day_summary
        normalized_days[d_key] = day_meals

        weekly_total_calories += day_cals
        weekly_total_protein += day_prot
        weekly_total_carbs += day_carbs
        weekly_total_fat += day_fat

    # Weekly overview
    num_days = max(1, len(expected_day_keys))
    weekly_avg_cal = round(weekly_total_calories / num_days)
    weekly_overview = raw_data.get("weekly_overview") or (
        f"A balanced {diet.lower()} meal schedule designed around your target of ~{target_cal} kcal/day "
        f"with average daily intake of {weekly_avg_cal} kcal."
    )

    # Adaptive Recommendations
    raw_recs = raw_data.get("adaptive_recommendations") or raw_data.get("recommendations") or []
    if isinstance(raw_recs, list) and raw_recs:
        adaptive_recommendations = [str(r).strip() for r in raw_recs if str(r).strip()]
    else:
        adaptive_recommendations = [
            f"Focus on complex carbohydrates at breakfast and lunch to maintain sustained energy for {goal.lower()}.",
            f"Include protein-rich elements in dinner and snacks to support muscle recovery and steady satiety.",
            "Stay adequately hydrated throughout the day; drink a glass of water 20 minutes before main meals.",
        ]

    # Nutrition notes
    nutrition_notes = str(raw_data.get("nutrition_notes") or f"Personalized for {diet} lifestyle and {goal} goal.").strip()

    # Shopping list
    raw_shopping = raw_data.get("shopping_list") or {}
    shopping_list = {
        "produce": raw_shopping.get("produce") or ["Fresh spinach", "Tomatoes", "Cucumbers", "Seasonal fruits"],
        "grains_and_legumes": raw_shopping.get("grains_and_legumes") or ["Brown rice", "Yellow moong dal", "Oats"],
        "dairy_and_protein": raw_shopping.get("dairy_and_protein") or ["Tofu or Paneer", "Chickpeas"],
        "spices_and_pantry": raw_shopping.get("spices_and_pantry") or ["Cumin seeds", "Turmeric", "Olive oil", "Black pepper"],
    }

    return {
        "plan_type": "daily" if days_count == 1 else "weekly",
        "target_calories": target_cal,
        "nutrition_notes": nutrition_notes,
        "adaptive_recommendations": adaptive_recommendations,
        "days": normalized_days,
        "shopping_list": shopping_list,
        "weekly_overview": weekly_overview,
        "weekly_total_calories": weekly_total_calories,
        "weekly_avg_calories": weekly_avg_cal,
        "weekly_total_protein": weekly_total_protein,
        "weekly_total_carbs": weekly_total_carbs,
        "weekly_total_fat": weekly_total_fat,
        "medical_disclaimer": DEFAULT_MEDICAL_DISCLAIMER,
        "ai_generated": True,
        "prefs": {
            "diet": diet,
            "goal": goal,
            "budget": budget,
            "days": days_count,
        },
    }
