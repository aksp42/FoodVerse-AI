"""
FoodVerse AI — Smart Kitchen Cooking Guidance and Recipe Generation Service
Smart Bridge Milestone 4, Activity 4.2

Provides:
  1. Contextual recipe generation via Gemini AI from ingredients (text or vision-identified),
     intended dish, cooking objective, cuisine, and skill level.
  2. Input validation and prompt engineering with clear safety guidelines.
  3. Structured response normalization with fallback defaults.
  4. Ingredient-image visual identification via Gemini Vision.
  5. Practical cooking guidance: prep/cook times, doneness cues, safety reminders.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from PIL import Image

# ---------------------------------------------------------------------------
# Default and Fallback Values
# ---------------------------------------------------------------------------

DEFAULT_SAFETY_REMINDERS = [
    "Wash hands thoroughly with soap for at least 20 seconds before preparing food.",
    "Ensure raw ingredients and ready-to-eat items are kept on separate cutting surfaces.",
    "Cook all ingredients to safe internal temperatures and reheat leftovers until steaming hot.",
    "Store perishable ingredients at or below 4 °C promptly after preparation.",
]

DEFAULT_COOKING_TIPS = [
    "Prep and measure all ingredients before heating the pan for smoother cooking.",
    "Taste and adjust seasonings gradually throughout the cooking process.",
    "Let hot pans heat properly before adding oil to prevent food from sticking.",
]


# ---------------------------------------------------------------------------
# Prompt Construction
# ---------------------------------------------------------------------------

def build_recipe_prompt(
    ingredients: List[str],
    diet: str = "Vegetarian",
    servings: int = 2,
    cuisine: str = "Indian",
    max_time_mins: int = 30,
    skill_level: str = "Beginner",
    cooking_objective: Optional[str] = None,
    intended_dish: Optional[str] = None,
    visual_identified_ingredients: Optional[List[str]] = None,
) -> str:
    """Build a comprehensive, structured prompt for Gemini LLM recipe generation."""
    ing_list = [i.strip() for i in ingredients if i and i.strip()]
    ing_str = ", ".join(ing_list[:25])

    context_lines = [
        f"Available Ingredients: {ing_str}",
        f"Dietary Constraint: {diet}",
        f"Cuisine Preference: {cuisine}",
        f"Target Servings: {servings}",
        f"Maximum Total Time: {max_time_mins} minutes",
        f"Cook Skill Level: {skill_level}",
    ]

    if intended_dish:
        context_lines.append(f"Intended Dish / Concept: {intended_dish}")
    if cooking_objective:
        context_lines.append(f"Cooking Objective / Goal: {cooking_objective}")
    if visual_identified_ingredients:
        context_lines.append(f"Ingredients Detected via Vision: {', '.join(visual_identified_ingredients)}")

    context_block = "\n".join(context_lines)

    return f"""You are a master culinary chef, kitchen safety mentor, and dietary consultant.
Create a structured, delicious, beginner-friendly recipe based strictly on this cooking context:

{context_block}

Return ONLY a valid JSON object matching this schema:
{{
  "name": "<clear, appealing recipe name>",
  "emoji": "<single food emoji matching dish>",
  "description": "<1-2 sentence description of flavour, texture, and appeal>",
  "prep_time_mins": <integer preparation time in minutes>,
  "cook_time_mins": <integer active cooking time in minutes>,
  "time": <total prep + cook time in minutes as integer>,
  "servings": {servings},
  "diet": "{diet.lower()}",
  "cuisine": "{cuisine}",
  "skill_level": "{skill_level}",
  "calories": <estimated calories per serving as integer>,
  "ingredients": [
    {{"n": "<ingredient name>", "q": "<precise quantity e.g. 200g, 1 tsp, 2 medium>"}}
  ],
  "steps": [
    "<Step 1 action with specific cutting/chopping technique>",
    "<Step 2 action with heat level and pan instruction>",
    "<Step 3 action with sensory doneness cue, e.g. until golden brown>",
    "<Step 4 action with simmering or sequence instruction>",
    "<Step 5 action with plating or resting guidance>"
  ],
  "cooking_tips": [
    "<actionable tip 1: chopping, temperature control, or texture>",
    "<actionable tip 2: sequence or flavor enhancement>"
  ],
  "substitutions": [
    "<practical ingredient swap if something is missing>"
  ],
  "food_safety_reminders": [
    "<essential hygiene, separation, or doneness temperature reminder>"
  ],
  "nutrition_tip": "<practical dietary and wellness note about this dish>",
  "assumptions": [
    "<any reasonable assumption made about staple availability or seasoning>"
  ]
}}

Rules:
1. Prioritize using the user's available ingredients. Common pantry staples (oil, water, salt, black pepper) may be assumed available.
2. Keep instructions numbered, chronological, clear, and beginner-accessible.
3. Every step MUST include practical guidance (e.g., heat setting 'medium-low', cutting style 'thinly sliced', or doneness cue 'until fragrant, ~2 minutes').
4. Include essential food safety reminders without making unscientific or unsupported health claims.
5. Strictly adhere to the dietary constraint: {diet}."""


def build_ingredient_vision_prompt() -> str:
    """Prompt for Gemini Vision to extract ingredients from a photograph."""
    return """You are a culinary vision assistant.
Analyze this photograph of food items, produce, pantry ingredients, or grocery haul.

Return ONLY a valid JSON object matching this schema:
{
  "is_food": true/false,
  "detected_ingredients": [
    "<ingredient 1 name>",
    "<ingredient 2 name>"
  ],
  "observations": "<brief description of the visible items and conditions>",
  "confidence_note": "<note on clarity and visibility of items>"
}

Rules:
- List only ingredients that are genuinely visible in the photograph.
- If no food or produce is visible, set "is_food": false and "detected_ingredients": [].
- Do NOT guess or hallucinate ingredients that cannot be seen."""


# ---------------------------------------------------------------------------
# Response Normalization
# ---------------------------------------------------------------------------

def normalize_recipe_response(
    raw_data: Optional[Dict[str, Any]],
    requested_servings: int = 2,
    requested_diet: str = "Vegetarian",
    cuisine: str = "Indian",
    model_used: str = "",
    visual_identified_ingredients: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Normalizes and validates recipe data returned from Gemini or fallbacks.
    Guarantees all required Activity 4.2 fields are present and safe for UI/PDF rendering.
    """
    if not isinstance(raw_data, dict):
        raw_data = {}

    name = str(raw_data.get("name") or "Custom Kitchen Creation").strip()
    emoji = str(raw_data.get("emoji") or "🍲").strip()
    description = str(raw_data.get("description") or "A wholesome dish crafted from your available kitchen ingredients.").strip()

    # Time calculations
    prep_time = raw_data.get("prep_time_mins")
    cook_time = raw_data.get("cook_time_mins")
    total_time = raw_data.get("time")

    try:
        prep_time = int(prep_time) if prep_time is not None else 10
    except (ValueError, TypeError):
        prep_time = 10

    try:
        cook_time = int(cook_time) if cook_time is not None else 20
    except (ValueError, TypeError):
        cook_time = 20

    try:
        total_time = int(total_time) if total_time is not None else (prep_time + cook_time)
    except (ValueError, TypeError):
        total_time = prep_time + cook_time

    # Servings & calories
    try:
        servings = int(raw_data.get("servings") or requested_servings)
    except (ValueError, TypeError):
        servings = requested_servings

    try:
        calories = int(raw_data.get("calories") or 350)
    except (ValueError, TypeError):
        calories = 350

    # Ingredients normalization
    raw_ingredients = raw_data.get("ingredients")
    ingredients_list: List[Dict[str, str]] = []
    if isinstance(raw_ingredients, list):
        for item in raw_ingredients:
            if isinstance(item, dict):
                n = str(item.get("n") or item.get("name") or "").strip()
                q = str(item.get("q") or item.get("quantity") or "to taste").strip()
                if n:
                    ingredients_list.append({"n": n, "q": q})
            elif isinstance(item, str) and item.strip():
                ingredients_list.append({"n": item.strip(), "q": "as required"})

    if not ingredients_list:
        ingredients_list = [{"n": "Available pantry ingredients", "q": "as prepared"}]

    # Steps normalization
    raw_steps = raw_data.get("steps")
    steps_list: List[str] = []
    if isinstance(raw_steps, list):
        for s in raw_steps:
            if isinstance(s, str) and s.strip():
                steps_list.append(s.strip())
            elif isinstance(s, dict) and s.get("step"):
                steps_list.append(str(s["step"]).strip())

    if not steps_list:
        steps_list = [
            "Wash, chop, and prepare all available vegetables and ingredients on a clean surface.",
            "Heat cooking oil in a skillet or pan over medium heat.",
            "Add prepared ingredients in order of cooking time, stirring occasionally until cooked through.",
            "Season to taste and serve warm."
        ]

    # Tips & substitutions
    tips = raw_data.get("cooking_tips")
    if not isinstance(tips, list) or not tips:
        tips = DEFAULT_COOKING_TIPS.copy()

    subs = raw_data.get("substitutions")
    if not isinstance(subs, list):
        subs = ["Staple herbs, spices, or cooking oil can be adjusted to personal preference."]

    # Safety reminders
    safety = raw_data.get("food_safety_reminders")
    if not isinstance(safety, list) or not safety:
        safety = DEFAULT_SAFETY_REMINDERS.copy()

    # Assumptions
    assumptions = raw_data.get("assumptions")
    if not isinstance(assumptions, list) or not assumptions:
        assumptions = ["Assumed common kitchen staples (salt, water, cooking oil) are available."]

    nutrition_tip = str(raw_data.get("nutrition_tip") or "Balanced meal providing energy and essential micronutrients.").strip()
    skill_level = str(raw_data.get("skill_level") or "Beginner").strip()

    engine = f"{model_used} LLM" if model_used else "Gemini LLM"

    return {
        "id": raw_data.get("id") or f"ai-{abs(hash(name)) % 100000}",
        "name": name,
        "emoji": emoji,
        "description": description,
        "prep_time_mins": prep_time,
        "cook_time_mins": cook_time,
        "time": total_time,
        "servings": servings,
        "diet": requested_diet.lower(),
        "cuisine": cuisine,
        "skill_level": skill_level,
        "calories": calories,
        "ingredients": ingredients_list,
        "steps": steps_list,
        "cooking_tips": tips,
        "substitutions": subs,
        "food_safety_reminders": safety,
        "nutrition_tip": nutrition_tip,
        "assumptions": assumptions,
        "ai_generated": True,
        "engine": engine,
        "visual_ingredients_detected": visual_identified_ingredients or [],
    }
