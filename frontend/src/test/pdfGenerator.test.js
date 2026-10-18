import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  generateMealPlanPDF,
  generateHygieneAuditPDF,
  generateFoodRecognitionPDF,
  generateFreshnessPDF,
  generateRecipePDF,
  generateActivityReportPDF,
} from '../utils/pdfGenerator';

// ── jsPDF mock ───────────────────────────────────────────────────────────────
// jsPDF attaches methods like .save() directly to instance closures, not to
// jsPDF.prototype. We mock the entire module so every `new jsPDF()` returns a
// controlled object with spyable methods.
vi.mock('jspdf', () => {
  const saveFn = vi.fn();

  function MockJsPDF() {
    // Minimal stubs for every jsPDF method called by pdfGenerator.js
    this.internal = {
      getNumberOfPages: () => 1,
      pageSize: {
        getWidth: () => 210,
        getHeight: () => 297,
      },
    };
    this.save = saveFn;
    this.addPage = vi.fn();
    this.setFillColor = vi.fn();
    this.setDrawColor = vi.fn();
    this.setTextColor = vi.fn();
    this.setFont = vi.fn();
    this.setFontSize = vi.fn();
    this.setLineWidth = vi.fn();
    this.rect = vi.fn();
    this.roundedRect = vi.fn();
    this.text = vi.fn();
    this.line = vi.fn();
    this.splitTextToSize = vi.fn((txt) => [String(txt)]);
    this.getTextWidth = vi.fn(() => 10);
    this.getStringUnitWidth = vi.fn(() => 1);
    this.setPage = vi.fn();
    this.output = vi.fn(() => '%PDF-1.3');
  }

  // Expose the saveFn so tests can assert on it
  MockJsPDF.__saveFn = saveFn;

  return { jsPDF: MockJsPDF };
});

// ── Helpers ──────────────────────────────────────────────────────────────────
async function getSaveFn() {
  const { jsPDF } = await import('jspdf');
  return jsPDF.__saveFn;
}

describe('FoodVerse AI — PDF Generator Suite', () => {
  let saveFn;

  beforeEach(async () => {
    vi.clearAllMocks();
    saveFn = await getSaveFn();
  });

  // ── 1. Meal Planner ────────────────────────────────────────────────────────
  describe('Meal Planner PDF Export', () => {
    it('generates a complete 7-day meal plan with short day keys (Mon, Tue, etc.) without errors', () => {
      const mockPlan = {
        prefs: { diet: 'Vegetarian', goal: 'Weight Loss', budget: 'Medium' },
        target_calories: 1600,
        ai_generated: true,
        engine: 'Gemini 3.8 Flash LLM',
        nutrition_notes: 'Focus on high dietary fiber, adequate hydration, and moderate complex carbohydrates.',
        days: {
          Mon: {
            breakfast: { name: 'Moong Dal Chilla with Mint Chutney', cal: 280, portion: '2 chillas (150g)', protein: 14, carbs: 38, fat: 6 },
            lunch: { name: 'Brown Rice, Toor Dal Tadka, and Cucumber Kachumber', cal: 540, portion: '1 bowl rice + 1 cup dal', protein: 20, carbs: 85, fat: 10 },
            dinner: { name: 'Palak Paneer with Multigrain Roti', cal: 480, portion: '150g paneer + 2 rotis', protein: 24, carbs: 50, fat: 16 },
            snack: { name: 'Roasted Makhana & Green Tea', cal: 150, portion: '1 small bowl (30g)', protein: 4, carbs: 22, fat: 3 },
          },
          Tue: {
            breakfast: { name: 'Oats Vegetable Upma', cal: 260, protein: 9, carbs: 44, fat: 5 },
            lunch: { name: 'Rajma Masala with Steamed Basmati Rice', cal: 560, protein: 22, carbs: 88, fat: 9 },
            dinner: { name: 'Tofu Bhurji Wrap', cal: 420, protein: 22, carbs: 42, fat: 14 },
          },
          Wed: {
            breakfast: { name: 'Poha with Roasted Peanuts', cal: 290 },
            lunch: { name: 'Chole Masala with Roti', cal: 520 },
            dinner: { name: 'Vegetable Khichdi with Curd', cal: 440 },
          },
          Thu: {
            breakfast: { name: 'Sprouted Moong Salad', cal: 210 },
            lunch: { name: 'Sambar, Brown Rice & Beans Poriyal', cal: 510 },
            dinner: { name: 'Mixed Veg Soup & Paneer Tikka', cal: 430 },
          },
          Fri: {
            breakfast: { name: 'Besan Chilla with Curd', cal: 310 },
            lunch: { name: 'Dal Makhani (Light) with Jeera Rice', cal: 550 },
            dinner: { name: 'Methi Thepla with Raita', cal: 420 },
          },
          Sat: {
            breakfast: { name: 'Idli with Sambar & Coconut Chutney', cal: 320 },
            lunch: { name: 'Paneer Pulao with Boondi Raita', cal: 580 },
            dinner: { name: 'Lauki Kofta (Baked) with Phulka', cal: 410 },
          },
          Sun: {
            breakfast: { name: 'Masala Dosa (Homemade)', cal: 340 },
            lunch: { name: 'Vegetable Biryani with Cucumber Raita', cal: 600 },
            dinner: { name: 'Moong Dal Khichdi with Roasted Papad', cal: 420 },
          },
        },
        shopping_list: {
          produce: ['Spinach', 'Coriander', 'Tomatoes', 'Onions', 'Cucumbers'],
          grains_and_legumes: ['Moong Dal', 'Brown Rice', 'Rajma', 'Rolled Oats'],
          dairy_and_protein: ['Paneer (500g)', 'Greek Yogurt', 'Tofu (200g)'],
          spices_and_pantry: ['Cumin Seeds', 'Turmeric', 'Garam Masala'],
        },
      };

      generateMealPlanPDF(mockPlan, {
        nutritionNote: mockPlan.nutrition_notes,
        goalCal: 1600,
        allergies: 'Lactose sensitivity',
      });

      expect(saveFn).toHaveBeenCalledWith('foodverse-7day-meal-plan.pdf');
    });

    it('safely handles empty or missing day keys and special characters', () => {
      const sparsePlan = {
        prefs: { diet: 'Jain & Keto <Special!>', goal: 'Muscle Gain', budget: 'Low' },
        days: {
          Mon: {
            breakfast: { name: 'Extremely Long Meal Name With Lots of Descriptive Text & Spices: Roasted Crunchy Moong Dal With Special Himalayan Pink Salt & Organic Cold Pressed Sesame Oil', cal: 350 },
          },
        },
      };

      expect(() => {
        generateMealPlanPDF(sparsePlan, { nutritionNote: '' });
      }).not.toThrow();

      expect(saveFn).toHaveBeenCalledWith('foodverse-7day-meal-plan.pdf');
    });
  });

  // ── 2. Hygiene Audit ───────────────────────────────────────────────────────
  describe('Hygiene Audit PDF Export', () => {
    it('generates an official hygiene audit report with scores, findings, and corrections', () => {
      const mockAudit = {
        score: 88,
        grade: 'Good',
        engine: 'Gemini 3.8 Flash Vision',
        summary: 'Commercial prep area shows diligent surface hygiene with minor equipment grease accumulation near fryers.',
        rubric_explanation: 'Scored against FSSAI and FDA visual commercial food facility hygiene codes.',
        findings: [
          { ok: true, text: 'Stainless steel work tables are sanitized and clear of food detritus.' },
          { ok: true, text: 'Raw and cooked ingredients are stored separately in sealed containers.' },
          { ok: false, text: 'Ventilation exhaust hood shows moderate grease residue requiring degreasing.' },
          { ok: true, text: 'Handwashing sink is unobstructed with soap and single-use towels.' },
        ],
        actionable_corrections: [
          'Schedule deep degreasing of the commercial exhaust hood within 48 hours.',
          'Verify date-labeling on secondary prep containers in walk-in cooler.',
        ],
        disclaimer: 'Advisory visual assessment. Not an official statutory inspection.',
      };

      generateHygieneAuditPDF(mockAudit, 'kitchen_station_1.jpg');
      expect(saveFn).toHaveBeenCalledWith('foodverse-hygiene-safety-audit.pdf');
    });
  });

  // ── 3. Food Recognition ────────────────────────────────────────────────────
  describe('Food Recognition PDF Export', () => {
    it('generates a nutrition breakdown report with macros and observations', () => {
      const mockRecognition = {
        predicted_class: 'Palak Paneer with Roti',
        confidence: 96,
        engine: 'Gemini 3.8 Flash Vision',
        description: 'Traditional North Indian spinach and cottage cheese gravy served alongside whole wheat flatbreads.',
        nutrition: {
          calories: 460,
          protein: 22,
          carbs: 48,
          fat: 18,
          fiber: 8,
          serving: '1 bowl gravy + 2 rotis (320g)',
          tip: 'Spinach provides excellent non-heme iron and folate; pairing with lemon juice optimizes mineral bioavailability.',
        },
        visual_observations: [
          'Rich vibrant green pureed spinach base with fresh ginger juliennes.',
          'Firm paneer cubes lightly seared without heavy oil separation.',
          'Whole wheat phulkas without excess ghee application.',
        ],
      };

      generateFoodRecognitionPDF(mockRecognition, 'palak_paneer.jpg');
      expect(saveFn).toHaveBeenCalledWith('foodverse-food-recognition-report.pdf');
    });
  });

  // ── 4. Freshness Detection ─────────────────────────────────────────────────
  describe('Freshness Detection PDF Export', () => {
    it('generates a freshness inspection report with safety checks and storage guidance', () => {
      const mockFreshness = {
        food_item: 'Fresh Strawberries',
        status: 'aging',
        label: 'Use Soon',
        certainty: 'High (94%)',
        engine: 'Gemini 3.8 Flash Vision',
        shelf: '1–2 days',
        observations: {
          color: 'Deep ruby red with minor softening at stem edges',
          texture: 'Slight loss of surface turgidity; no fungal mycelium',
          defects: 'Mild pressure bruising on two berries',
        },
        checks: [
          { ok: true, text: 'No visible mold, white fungal fluff, or spore patches detected.' },
          { ok: false, text: 'Surface softening suggests approaching end of optimal shelf life.' },
          { ok: true, text: 'Calyx leaves remain green and intact.' },
        ],
        recommendations: [
          'Consume within 24 hours or blend into a smoothie.',
          'Keep dry and unwashed in breathable refrigeration at 2–4°C.',
          'Discard any individual berry that develops fuzzy white mold.',
        ],
        disclaimer: 'Visual assessment only. Wash produce thoroughly before consumption.',
      };

      generateFreshnessPDF(mockFreshness, 'strawberries.jpg');
      expect(saveFn).toHaveBeenCalledWith('foodverse-freshness-inspection.pdf');
    });
  });

  // ── 5. Cooking Assistant ───────────────────────────────────────────────────
  describe('Cooking Assistant Recipe PDF Export', () => {
    it('generates a formatted recipe PDF with ingredients and numbered cooking steps', () => {
      const mockRecipe = {
        name: 'Spiced Chickpea & Spinach Stew',
        diet: 'Vegan',
        time: 25,
        servings: 3,
        calories: 340,
        description: 'A comforting, one-pot protein-rich curry featuring boiled chickpeas simmered with aromatic garam masala and tender baby spinach.',
        ingredients: [
          { n: 'Cooked Chickpeas (Kabuli Chana)', q: '2 cups (350g)' },
          { n: 'Baby Spinach leaves', q: '3 cups packed' },
          { n: 'Diced Tomatoes', q: '2 medium' },
          { n: 'Grated Ginger & Garlic', q: '1 tbsp each' },
          { n: 'Cumin seeds & Garam masala', q: '1 tsp each' },
        ],
        steps: [
          'Heat 1 tbsp oil in a heavy-bottomed pot over medium heat and crackle the cumin seeds.',
          'Add chopped onions, ginger, and garlic; sauté until aromatic and translucent (approx. 4 mins).',
          'Stir in diced tomatoes, turmeric, ground coriander, and salt. Cook until tomatoes soften into a cohesive gravy.',
          'Fold in the boiled chickpeas and 1 cup of warm water; simmer on low heat for 10 minutes allowing the flavors to infuse.',
          'Add fresh spinach leaves during the final 3 minutes of cooking, stirring gently until wilted.',
          'Garnish with freshly squeezed lemon juice and chopped cilantro before serving.',
        ],
        nutrition_tip: 'Chickpeas provide high biological value plant protein and slowly digestible resistant starch for prolonged satiety.',
      };

      generateRecipePDF(mockRecipe);
      expect(saveFn).toHaveBeenCalled();
      const savedFilename = saveFn.mock.calls[0][0];
      expect(savedFilename).toContain('spiced-chickpea');
    });
  });

  // ── 6. Activity Report ─────────────────────────────────────────────────────
  describe('Activity & Nutrition Report PDF Export', () => {
    it('generates a user activity summary from SQLite logs', () => {
      const mockData = {
        user: { name: 'Akanksha Singh', email: 'akanksha@foodverse.ai' },
        profile: { diet: 'Vegetarian', goal: 'Muscle Gain' },
        stats: { meals: 14, calories: 2150, totalScans: 28 },
        calorieGoal: 2200,
        progress: 98,
        activity: [
          { id: '1', type: 'food', text: 'Identified Paneer Tikka (380 kcal)', ts: Date.now() - 3600000 },
          { id: '2', type: 'freshness', text: 'Evaluated Spinach (Fresh - 4 days)', ts: Date.now() - 7200000 },
          { id: '3', type: 'hygiene', text: 'Kitchen Hygiene Audit: Score 92/100', ts: Date.now() - 86400000 },
          { id: '4', type: 'cook', text: 'Cooked Dal Tadka (320 kcal)', ts: Date.now() - 172800000 },
          { id: '5', type: 'plan', text: 'Generated 7-Day AI Meal Plan (Vegetarian)', ts: Date.now() - 259200000 },
        ],
      };

      generateActivityReportPDF(mockData);
      expect(saveFn).toHaveBeenCalledWith('foodverse-activity-report.pdf');
    });

    it('safely handles empty activity logs without throwing errors', () => {
      expect(() => {
        generateActivityReportPDF({
          user: null,
          profile: null,
          stats: { meals: 0, calories: 0 },
          calorieGoal: 1900,
          progress: 0,
          activity: [],
        });
      }).not.toThrow();

      expect(saveFn).toHaveBeenCalledWith('foodverse-activity-report.pdf');
    });
  });
});
