import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { GOAL_CALORIES } from '../data/mock';
import { loadJSON, saveJSON } from '../utils/helpers';
import { fetchDashboardMetrics, fetchRecentActivities } from '../utils/analysis';
import { useAuth } from './AuthContext';

const AppDataContext = createContext(null);
const KEY = 'fv_appdata_v2';

const DEFAULTS = {
  profile: {
    phone: '',
    diet: 'Vegetarian',
    goal: 'Weight Maintain',
    budget: 'Medium',
    allergies: '',
    intolerances: '',
    dislikes: '',
    restrictions: '',
    age: '',
    height_cm: '',
    weight_kg: '',
    gender: 'unspecified',
    activity_level: 'moderately active',
    avatar: '',
  },
  settings: {
    mealReminders: true,
    freshnessAlerts: true,
    weeklyReport: false,
    emailUpdates: false,
    compactMode: false,
  },
  // Clean operational state: starts empty, populated from SQLite
  activity: [],
  stats: { meals: 0, calories: 0, totalScans: 0 },
  todayMacros: { protein: 0, carbs: 0, fat: 0 },
  hasTodayMeals: false,
  categoryDistribution: [],
  weeklyCalories: [
    { day: 'Mon', calories: 0 },
    { day: 'Tue', calories: 0 },
    { day: 'Wed', calories: 0 },
    { day: 'Thu', calories: 0 },
    { day: 'Fri', calories: 0 },
    { day: 'Sat', calories: 0 },
    { day: 'Sun', calories: 0 },
  ],
  macroSplit: [
    { name: 'Carbs', value: 50, color: '#fbb03b', grams: 0 },
    { name: 'Protein', value: 25, color: '#4aa83a', grams: 0 },
    { name: 'Fat', value: 25, color: '#14532d', grams: 0 },
  ],
  pantry: ['Tomato', 'Onion', 'Garlic', 'Capsicum', 'Paneer', 'Potato', 'Spices'],
  savedRecipes: [],
  mealPlan: null,
};

export function AppDataProvider({ children }) {
  const { user } = useAuth();
  const storageKey = user ? `${KEY}:${user.email}` : KEY;

  const [data, setData] = useState(() => ({ ...DEFAULTS, ...loadJSON(storageKey, {}) }));

  // Load real metrics and activity logs from SQLite backend
  const refreshFromBackend = useCallback(async () => {
    try {
      const [statsRes, activitiesRes] = await Promise.allSettled([
        fetchDashboardMetrics(),
        fetchRecentActivities(15)
      ]);

      setData((prev) => {
        let newStats = prev.stats;
        let newWeekly = prev.weeklyCalories;
        let newMacro = prev.macroSplit;
        let newAct = prev.activity;
        let newTodayMacros = prev.todayMacros || { protein: 0, carbs: 0, fat: 0 };
        let newHasTodayMeals = prev.hasTodayMeals || false;
        let newCategoryDist = prev.categoryDistribution || [];

        if (statsRes.status === 'fulfilled' && statsRes.value) {
          const s = statsRes.value;
          newStats = { 
            meals: s.total_meals || 0, 
            calories: s.today_calories || 0,
            totalScans: s.total_scans ?? s.total_meals ?? 0
          };
          if (Array.isArray(s.weekly_calories)) newWeekly = s.weekly_calories;
          if (Array.isArray(s.macro_split)) newMacro = s.macro_split;
          if (s.today_macros) newTodayMacros = s.today_macros;
          if (Array.isArray(s.category_distribution)) newCategoryDist = s.category_distribution;
          newHasTodayMeals = !!s.has_today_meals;
        }

        if (activitiesRes.status === 'fulfilled' && Array.isArray(activitiesRes.value)) {
          newAct = activitiesRes.value.map((a) => ({
            id: a.id,
            type: a.module,
            text: a.title,
            ts: new Date(a.created_at).getTime(),
          }));
        }

        return {
          ...prev,
          stats: newStats,
          weeklyCalories: newWeekly,
          macroSplit: newMacro,
          activity: newAct,
          todayMacros: newTodayMacros,
          hasTodayMeals: newHasTodayMeals,
          categoryDistribution: newCategoryDist,
        };
      });
    } catch {
      // Backend offline: keep current local data
    }
  }, []);

  useEffect(() => {
    refreshFromBackend();
  }, [refreshFromBackend]);

  useEffect(() => {
    saveJSON(storageKey, data);
  }, [data, storageKey]);

  const updateProfile = useCallback((patch) => setData((d) => ({ ...d, profile: { ...d.profile, ...patch } })), []);
  const updateSettings = useCallback((patch) => setData((d) => ({ ...d, settings: { ...d.settings, ...patch } })), []);

  const addActivity = useCallback((type, text, statsPatch) => {
    setData((d) => ({
      ...d,
      activity: [{ id: `${Date.now()}-${Math.random().toString(36).slice(2, 6)}`, type, text, ts: Date.now() }, ...d.activity].slice(0, 30),
      stats: statsPatch ? { meals: d.stats.meals + (statsPatch.meals || 0), calories: d.stats.calories + (statsPatch.calories || 0) } : d.stats,
    }));
    // Also trigger backend refresh
    setTimeout(refreshFromBackend, 400);
  }, [refreshFromBackend]);

  const clearActivity = useCallback(() => setData((d) => ({ ...d, activity: [] })), []);
  const setPantry = useCallback((fn) => setData((d) => ({ ...d, pantry: typeof fn === 'function' ? fn(d.pantry) : fn })), []);
  const toggleSavedRecipe = useCallback((id) => setData((d) => ({
    ...d,
    savedRecipes: d.savedRecipes.includes(id) ? d.savedRecipes.filter((x) => x !== id) : [...d.savedRecipes, id],
  })), []);
  const setMealPlan = useCallback((plan) => setData((d) => ({ ...d, mealPlan: plan })), []);

  const calorieGoal = GOAL_CALORIES[data.profile.goal] || 1900;
  const progress = Math.min(100, Math.round((data.stats.calories / calorieGoal) * 100));

  const value = useMemo(() => ({
    ...data, calorieGoal, progress, refreshFromBackend,
    updateProfile, updateSettings, addActivity, clearActivity, setPantry, toggleSavedRecipe, setMealPlan,
  }), [data, calorieGoal, progress, refreshFromBackend, updateProfile, updateSettings, addActivity, clearActivity, setPantry, toggleSavedRecipe, setMealPlan]);

  return <AppDataContext.Provider value={value}>{children}</AppDataContext.Provider>;
}

export function useAppData() {
  const ctx = useContext(AppDataContext);
  if (!ctx) throw new Error('useAppData must be used inside AppDataProvider');
  return ctx;
}
