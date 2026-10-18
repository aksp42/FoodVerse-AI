import '@testing-library/jest-dom/vitest';
import { afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';

class RO { observe() {} unobserve() {} disconnect() {} }
globalThis.ResizeObserver = globalThis.ResizeObserver || RO;
window.scrollTo = () => {};
if (!URL.createObjectURL) URL.createObjectURL = () => 'blob:mock';
if (!URL.revokeObjectURL) URL.revokeObjectURL = () => {};

globalThis.fetch = vi.fn(async (url) => {
  const u = String(url);
  if (u.includes('/api/dashboard/stats')) {
    return {
      ok: true,
      json: async () => ({
        total_meals: 3,
        today_calories: 650,
        weekly_calories: [
          { day: 'Mon', calories: 450 },
          { day: 'Tue', calories: 200 },
          { day: 'Wed', calories: 0 },
          { day: 'Thu', calories: 0 },
          { day: 'Fri', calories: 0 },
          { day: 'Sat', calories: 0 },
          { day: 'Sun', calories: 0 },
        ],
        macro_split: [
          { name: 'Carbs', value: 50, color: '#fbb03b' },
          { name: 'Protein', value: 25, color: '#4aa83a' },
          { name: 'Fat', value: 25, color: '#14532d' }
        ]
      })
    };
  }
  if (u.includes('/api/activities')) {
    return {
      ok: true,
      json: async () => [
        { id: 1, module: 'food', title: 'Identified: Biryani', created_at: new Date().toISOString() }
      ]
    };
  }
  if (u.includes('/api/meal-plan')) {
    return {
      ok: true,
      json: async () => ({
        target_calories: 1900,
        nutrition_notes: 'Balanced macro nutrient profile across the week.',
        ai_generated: true,
        engine: 'Gemini 3.8 Flash LLM',
        days: {
          Mon: {
            breakfast: { name: 'Poha', emoji: '🥣', cal: 350, diets: ['Vegetarian'], cost: 'Medium' },
            lunch: { name: 'Dal Chawal', emoji: '🍛', cal: 650, diets: ['Vegetarian'], cost: 'Medium' },
            dinner: { name: 'Palak Paneer', emoji: '🥘', cal: 550, diets: ['Vegetarian'], cost: 'Medium' }
          },
          Tue: {
            breakfast: { name: 'Upma', emoji: '🥣', cal: 320, diets: ['Vegetarian'], cost: 'Medium' },
            lunch: { name: 'Rajma Chawal', emoji: '🍛', cal: 680, diets: ['Vegetarian'], cost: 'Medium' },
            dinner: { name: 'Roti Dal', emoji: '🫓', cal: 500, diets: ['Vegetarian'], cost: 'Medium' }
          },
          Wed: {
            breakfast: { name: 'Idli Sambar', emoji: '🥞', cal: 300, diets: ['Vegetarian'], cost: 'Medium' },
            lunch: { name: 'Chole Roti', emoji: '🍛', cal: 650, diets: ['Vegetarian'], cost: 'Medium' },
            dinner: { name: 'Khichdi', emoji: '🍲', cal: 480, diets: ['Vegetarian'], cost: 'Medium' }
          },
          Thu: {
            breakfast: { name: 'Moong Cheela', emoji: '🥞', cal: 340, diets: ['Vegetarian'], cost: 'Medium' },
            lunch: { name: 'Kadhi Chawal', emoji: '🍛', cal: 620, diets: ['Vegetarian'], cost: 'Medium' },
            dinner: { name: 'Mix Veg Roti', emoji: '🫓', cal: 520, diets: ['Vegetarian'], cost: 'Medium' }
          },
          Fri: {
            breakfast: { name: 'Besan Chilla', emoji: '🥞', cal: 330, diets: ['Vegetarian'], cost: 'Medium' },
            lunch: { name: 'Biryani Raita', emoji: '🍚', cal: 700, diets: ['Vegetarian'], cost: 'Medium' },
            dinner: { name: 'Dalia', emoji: '🍲', cal: 450, diets: ['Vegetarian'], cost: 'Medium' }
          },
          Sat: {
            breakfast: { name: 'Dosa Sambar', emoji: '🥞', cal: 380, diets: ['Vegetarian'], cost: 'Medium' },
            lunch: { name: 'Paneer Bhurji Roti', emoji: '🫓', cal: 680, diets: ['Vegetarian'], cost: 'Medium' },
            dinner: { name: 'Soup & Toast', emoji: '🥣', cal: 420, diets: ['Vegetarian'], cost: 'Medium' }
          },
          Sun: {
            breakfast: { name: 'Stuffed Paratha', emoji: '🫓', cal: 450, diets: ['Vegetarian'], cost: 'Medium' },
            lunch: { name: 'Special Thali', emoji: '🍱', cal: 750, diets: ['Vegetarian'], cost: 'Medium' },
            dinner: { name: 'Light Salad & Dal', emoji: '🥗', cal: 450, diets: ['Vegetarian'], cost: 'Medium' }
          }
        }
      })
    };
  }
  if (u.includes('/api/freshness')) {
    return {
      ok: true,
      json: async () => ({
        status: 'fresh',
        label: 'Fresh',
        certainty: 'High',
        food_item: 'Fresh Tomato',
        shelf: '4-5 days if refrigerated',
        observations: { color: 'Vibrant red', texture: 'Firm skin', defects: 'None' },
        checks: [
          { ok: true, text: 'Surface integrity intact' },
          { ok: true, text: 'No visible spoilage' }
        ],
        recommendations: ['Store at room temperature or chill']
      })
    };
  }
  return {
    ok: true,
    json: async () => ({ status: 'ok' })
  };
});

afterEach(() => { cleanup(); localStorage.clear(); });
