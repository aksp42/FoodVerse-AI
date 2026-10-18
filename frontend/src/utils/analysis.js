/**
 * FoodVerse AI — Analysis & API Client Layer
 * Handles communication with FastAPI backend endpoints:
 * - Food Recognition (Exclusively powered by Gemini Vision)
 * - Freshness Detection (Gemini Vision)
 * - Restaurant Hygiene Inspection (Gemini Vision)
 * - Smart Cooking Assistant (Gemini LLM)
 * - Personalized Meal Planner (Gemini LLM)
 * - Real Dashboard Analytics & Activities (SQLite)
 */

// ── 1. Food Recognition — Gemini Vision ──────────────────────────────────────
/**
 * Sends food photograph to FastAPI backend for recognition using Gemini Vision.
 * @param {File} file 
 */
export async function analyzeFood(file) {
  const form = new FormData();
  form.append('image', file);

  const res = await fetch('/api/predict', { method: 'POST', body: form });

  if (!res.ok) {
    let msg = 'Food recognition failed';
    try {
      const body = await res.json();
      if (body?.detail) msg = body.detail;
      else if (body?.error) msg = body.error;
    } catch { /* ignore */ }
    throw new Error(msg);
  }

  return res.json();
}

// ── 2. Food Freshness & Spoilage Detection — Gemini Vision ───────────────────
export async function analyzeFreshness(file) {
  const form = new FormData();
  form.append('image', file);

  const res = await fetch('/api/freshness', { method: 'POST', body: form });

  if (!res.ok) {
    let msg = 'Freshness analysis failed';
    try {
      const body = await res.json();
      if (body?.detail) msg = body.detail;
    } catch { /* ignore */ }
    throw new Error(msg);
  }

  const data = await res.json();
  if (!Array.isArray(data.checks)) {
    data.checks = [
      { ok: data.status !== 'spoiled', text: `Visual evaluation: ${data.label}` },
      { ok: true, text: `Estimated shelf life: ${data.shelf || 'Check daily'}` }
    ];
  }
  return data;
}

// ── 3. Restaurant Hygiene & Kitchen Safety — Gemini Vision ───────────────────
export async function analyzeHygiene(file) {
  const form = new FormData();
  form.append('image', file);

  const res = await fetch('/api/hygiene', { method: 'POST', body: form });

  if (!res.ok) {
    let msg = 'Hygiene inspection failed';
    try {
      const body = await res.json();
      if (body?.detail) msg = body.detail;
    } catch { /* ignore */ }
    throw new Error(msg);
  }

  const data = await res.json();
  if (!Array.isArray(data.findings)) {
    data.findings = [
      { ok: data.score >= 70, text: 'Cleanliness of visible food surfaces' },
      { ok: data.score >= 75, text: 'Food storage and organization' }
    ];
  }
  return data;
}

// ── 4. Smart Cooking — Gemini LLM Recipe Generation (Activity 4.2) ──────────
export async function generateAIRecipe(ingredients, diet = 'Vegetarian', servings = 2, cuisine = 'Indian', options = {}) {
  const payload = {
    ingredients,
    diet,
    servings,
    cuisine,
    max_time_mins: options.max_time_mins || 30,
    skill_level: options.skill_level || 'Beginner',
    cooking_objective: options.cooking_objective || null,
    intended_dish: options.intended_dish || null,
    visual_identified_ingredients: options.visual_identified_ingredients || null,
  };

  const res = await fetch('/api/cooking', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    let msg = 'Recipe generation failed';
    try {
      const body = await res.json();
      if (body?.detail) msg = body.detail;
    } catch { /* ignore */ }
    throw new Error(msg);
  }

  return res.json();
}

export async function detectIngredientsFromImage(file) {
  const form = new FormData();
  form.append('image', file);

  const res = await fetch('/api/cooking/detect-ingredients', {
    method: 'POST',
    body: form,
  });

  if (!res.ok) {
    let msg = 'Ingredient image detection failed';
    try {
      const body = await res.json();
      if (body?.detail) msg = body.detail;
    } catch { /* ignore */ }
    throw new Error(msg);
  }

  return res.json();
}

// ── User Profile API (Activity 5.1) ──────────────────────────────────────────
export async function saveUserProfileAPI(profileData, userId = 'default_user') {
  const res = await fetch('/api/profile', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...profileData, user_id: userId }),
  });

  if (!res.ok) {
    let msg = 'Profile save failed';
    try {
      const body = await res.json();
      if (body?.detail) {
        msg = typeof body.detail === 'string' ? body.detail : (body.detail.message || JSON.stringify(body.detail));
        if (body.detail.errors) msg += ': ' + body.detail.errors.join('; ');
      }
    } catch { /* ignore */ }
    throw new Error(msg);
  }

  return res.json();
}

export async function fetchUserProfileAPI(userId = 'default_user') {
  const res = await fetch(`/api/profile?user_id=${encodeURIComponent(userId)}`);
  if (!res.ok) {
    throw new Error('Failed to load profile from server');
  }
  return res.json();
}

// ── 5. Personalized Meal Planner — Gemini LLM (Activity 5.2) ─────────────────
export async function generateAIMealPlan(diet, goal, budget, allergies = '', days = 7, userId = 'default_user') {
  const res = await fetch('/api/meal-plan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, diet, goal, budget, allergies, days }),
  });

  if (!res.ok) {
    let msg = 'Meal plan generation failed';
    try {
      const body = await res.json();
      if (body?.detail) msg = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
    } catch { /* ignore */ }
    throw new Error(msg);
  }

  return res.json();
}

export async function fetchSavedMealPlan(userId = 'default_user') {
  const res = await fetch(`/api/meal-plan?user_id=${encodeURIComponent(userId)}`);
  if (!res.ok) {
    throw new Error('Failed to fetch saved meal plan from server');
  }
  return res.json();
}

// ── 6. Real Dashboard Statistics & Activity from SQLite ───────────────────────
export async function fetchDashboardMetrics() {
  const res = await fetch('/api/dashboard/stats');
  if (!res.ok) {
    throw new Error('Failed to fetch dashboard metrics');
  }
  return res.json();
}

export async function fetchRecentActivities() {
  const res = await fetch('/api/activities');
  if (!res.ok) {
    throw new Error('Failed to fetch activity logs');
  }
  return res.json();
}

// ── Utility ───────────────────────────────────────────────────────────────────
export function scaleNutrition(food, factor) {
  const r = (n) => Math.round(n * factor);
  return {
    calories: r(food.calories || 0),
    protein:  r(food.protein || 0),
    carbs:    r(food.carbs || 0),
    fat:      r(food.fat || 0),
    fiber:    r(food.fiber || 0),
  };
}
