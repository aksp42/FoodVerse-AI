// Realistic mock data — swap these with API calls once the backend exists.

export const FOODS = [
  { id: 'paneer-tikka', name: 'Paneer Tikka', emoji: '🍢', cuisine: 'North Indian', confidence: 95, calories: 320, protein: 24, carbs: 12, fat: 16, fiber: 3, serving: '1 plate (180 g)', tags: ['vegetarian', 'high-protein'], tip: 'Great protein source. Pair with a mint salad to balance the fat.' },
  { id: 'avocado-bowl', name: 'Avocado Chickpea Bowl', emoji: '🥑', cuisine: 'Mediterranean', confidence: 92, calories: 410, protein: 15, carbs: 46, fat: 19, fiber: 12, serving: '1 bowl (320 g)', tags: ['vegan', 'high-fiber'], tip: 'Rich in healthy fats and fiber — keeps you full for hours.' },
  { id: 'masala-dosa', name: 'Masala Dosa', emoji: '🥞', cuisine: 'South Indian', confidence: 90, calories: 380, protein: 8, carbs: 58, fat: 13, fiber: 4, serving: '1 dosa with filling', tags: ['vegetarian'], tip: 'Ask for less oil and add sambar for extra protein and fiber.' },
  { id: 'veg-biryani', name: 'Vegetable Biryani', emoji: '🍛', cuisine: 'Indian', confidence: 93, calories: 450, protein: 11, carbs: 72, fat: 14, fiber: 6, serving: '1 plate (300 g)', tags: ['vegetarian'], tip: 'Add a bowl of raita and salad to balance the carbohydrates.' },
  { id: 'greek-salad', name: 'Greek Salad', emoji: '🥗', cuisine: 'Greek', confidence: 94, calories: 210, protein: 7, carbs: 11, fat: 15, fiber: 4, serving: '1 bowl (250 g)', tags: ['vegetarian', 'low-carb'], tip: 'Light and hydrating. Add chickpeas for a more filling meal.' },
  { id: 'margherita', name: 'Margherita Pizza', emoji: '🍕', cuisine: 'Italian', confidence: 96, calories: 540, protein: 22, carbs: 66, fat: 20, fiber: 4, serving: '2 slices', tags: ['vegetarian'], tip: 'Pair with a side salad and keep it to two slices for a balanced meal.' },
  { id: 'grilled-chicken', name: 'Grilled Chicken Plate', emoji: '🍗', cuisine: 'Continental', confidence: 91, calories: 360, protein: 42, carbs: 14, fat: 14, fiber: 3, serving: '1 plate (260 g)', tags: ['high-protein', 'low-carb'], tip: 'Excellent lean protein. Add roasted vegetables for micronutrients.' },
  { id: 'fruit-bowl', name: 'Fresh Fruit Bowl', emoji: '🍓', cuisine: 'Healthy', confidence: 97, calories: 150, protein: 2, carbs: 36, fat: 1, fiber: 6, serving: '1 bowl (250 g)', tags: ['vegan', 'low-fat'], tip: 'Naturally sweet and full of vitamin C. Great as a snack.' },
];

// UI configuration constants and fallback templates for offline/demo operation.


export const PANTRY_SUGGESTIONS = ['Tomato', 'Onion', 'Garlic', 'Capsicum', 'Paneer', 'Potato', 'Spices', 'Rice', 'Spinach', 'Chickpeas', 'Carrot', 'Peas', 'Yogurt', 'Eggs', 'Mushroom', 'Lentils', 'Cauliflower', 'Chicken', 'Pasta', 'Cheese'];

export const RECIPES = [
  { id: 'paneer-masala', name: 'Paneer Masala', emoji: '🍛', time: 30, servings: 4, diet: 'vegetarian', calories: 320,
    ingredients: [{ n: 'Paneer', q: '200g' }, { n: 'Tomato', q: '2' }, { n: 'Onion', q: '1' }, { n: 'Garlic', q: '4 cloves' }, { n: 'Spices', q: 'to taste' }, { n: 'Capsicum', q: '1' }],
    steps: ['Marinate paneer with spices.', 'Sauté onion, garlic and capsicum until soft.', 'Add tomato and cook into a thick masala.', 'Fold in paneer and simmer for 5 minutes.', 'Serve hot with roti or rice.'] },
  { id: 'veg-stir-fry', name: 'Garlic Veg Stir-Fry', emoji: '🥘', time: 15, servings: 2, diet: 'vegan', calories: 210,
    ingredients: [{ n: 'Capsicum', q: '1' }, { n: 'Carrot', q: '1' }, { n: 'Peas', q: '½ cup' }, { n: 'Garlic', q: '3 cloves' }, { n: 'Onion', q: '1' }, { n: 'Spices', q: 'to taste' }],
    steps: ['Heat oil and sauté garlic for 30 seconds.', 'Add onion, carrot and peas; stir-fry on high heat.', 'Add capsicum and spices.', 'Cook 3–4 minutes so the vegetables stay crunchy.', 'Serve with rice or noodles.'] },
  { id: 'aloo-sabzi', name: 'Jeera Aloo', emoji: '🥔', time: 25, servings: 3, diet: 'vegan', calories: 240,
    ingredients: [{ n: 'Potato', q: '3' }, { n: 'Onion', q: '1' }, { n: 'Tomato', q: '1' }, { n: 'Spices', q: 'to taste' }],
    steps: ['Boil and cube the potatoes.', 'Temper cumin seeds in hot oil.', 'Add onion and tomato; cook until soft.', 'Toss in potatoes and spices.', 'Garnish with coriander and serve.'] },
  { id: 'tomato-soup', name: 'Roasted Tomato Soup', emoji: '🍅', time: 35, servings: 3, diet: 'vegan', calories: 140,
    ingredients: [{ n: 'Tomato', q: '5' }, { n: 'Garlic', q: '3 cloves' }, { n: 'Onion', q: '1' }, { n: 'Spices', q: 'to taste' }],
    steps: ['Roast tomatoes, garlic and onion for 20 minutes.', 'Blend until smooth.', 'Simmer with spices for 5 minutes.', 'Strain for a silky texture.', 'Serve with a drizzle of olive oil.'] },
  { id: 'palak-paneer', name: 'Palak Paneer', emoji: '🥬', time: 30, servings: 3, diet: 'vegetarian', calories: 290,
    ingredients: [{ n: 'Spinach', q: '2 bunches' }, { n: 'Paneer', q: '200g' }, { n: 'Onion', q: '1' }, { n: 'Garlic', q: '4 cloves' }, { n: 'Tomato', q: '1' }, { n: 'Spices', q: 'to taste' }],
    steps: ['Blanch spinach and blend to a puree.', 'Sauté onion, garlic and tomato.', 'Add the spinach puree and spices.', 'Add paneer cubes and simmer 5 minutes.', 'Finish with a swirl of cream or yogurt.'] },
  { id: 'chana-masala', name: 'Chana Masala', emoji: '🫘', time: 40, servings: 4, diet: 'vegan', calories: 310,
    ingredients: [{ n: 'Chickpeas', q: '2 cups' }, { n: 'Onion', q: '2' }, { n: 'Tomato', q: '2' }, { n: 'Garlic', q: '4 cloves' }, { n: 'Spices', q: 'to taste' }],
    steps: ['Pressure-cook soaked chickpeas until tender.', 'Make a masala with onion, garlic and tomato.', 'Add chickpeas and spices.', 'Simmer for 15 minutes.', 'Serve with rice or bhatura.'] },
  { id: 'egg-bhurji', name: 'Masala Egg Bhurji', emoji: '🍳', time: 12, servings: 2, diet: 'non-veg', calories: 260,
    ingredients: [{ n: 'Eggs', q: '4' }, { n: 'Onion', q: '1' }, { n: 'Tomato', q: '1' }, { n: 'Capsicum', q: '½' }, { n: 'Spices', q: 'to taste' }],
    steps: ['Sauté onion, tomato and capsicum.', 'Add spices.', 'Crack in eggs and scramble on medium heat.', 'Cook until just set.', 'Serve with toast or paratha.'] },
  { id: 'veg-pulao', name: 'Vegetable Pulao', emoji: '🍚', time: 30, servings: 3, diet: 'vegan', calories: 330,
    ingredients: [{ n: 'Rice', q: '1 cup' }, { n: 'Peas', q: '½ cup' }, { n: 'Carrot', q: '1' }, { n: 'Onion', q: '1' }, { n: 'Spices', q: 'to taste' }],
    steps: ['Rinse and soak rice for 15 minutes.', 'Sauté whole spices and onion.', 'Add vegetables and rice.', 'Add water, cover and cook until fluffy.', 'Rest 5 minutes before serving.'] },
  { id: 'mushroom-garlic', name: 'Garlic Mushrooms', emoji: '🍄', time: 15, servings: 2, diet: 'vegan', calories: 150,
    ingredients: [{ n: 'Mushroom', q: '250g' }, { n: 'Garlic', q: '5 cloves' }, { n: 'Spices', q: 'to taste' }, { n: 'Onion', q: '½' }],
    steps: ['Slice the mushrooms.', 'Sauté garlic in butter or oil.', 'Add mushrooms on high heat until golden.', 'Season with pepper and herbs.', 'Serve on toast or as a side.'] },
  { id: 'cheese-pasta', name: 'Creamy Veg Pasta', emoji: '🍝', time: 25, servings: 2, diet: 'vegetarian', calories: 480,
    ingredients: [{ n: 'Pasta', q: '200g' }, { n: 'Cheese', q: '½ cup' }, { n: 'Capsicum', q: '1' }, { n: 'Garlic', q: '3 cloves' }, { n: 'Mushroom', q: '100g' }],
    steps: ['Boil pasta until al dente.', 'Sauté garlic, mushrooms and capsicum.', 'Add cheese and a splash of pasta water.', 'Toss in the pasta.', 'Finish with herbs and chili flakes.'] },
];

export const DIETS = ['Vegetarian', 'Vegan', 'Non-Vegetarian', 'Eggetarian', 'Keto', 'Jain'];
export const GOALS = ['Weight Loss', 'Weight Maintain', 'Muscle Gain', 'Heart Healthy'];
export const BUDGETS = ['Low', 'Medium', 'High'];
export const GOAL_CALORIES = { 'Weight Loss': 1500, 'Weight Maintain': 1900, 'Muscle Gain': 2400, 'Heart Healthy': 1800 };

export const MEAL_POOL = {
  breakfast: [
    { name: 'Oats Bowl', emoji: '🥣', cal: 280, diets: ['Vegetarian', 'Vegan', 'Eggetarian', 'Non-Vegetarian', 'Jain'], cost: 'Low' },
    { name: 'Poha', emoji: '🍚', cal: 250, diets: ['Vegetarian', 'Vegan', 'Eggetarian', 'Non-Vegetarian', 'Jain'], cost: 'Low' },
    { name: 'Veg Upma', emoji: '🥘', cal: 260, diets: ['Vegetarian', 'Vegan', 'Eggetarian', 'Non-Vegetarian'], cost: 'Low' },
    { name: 'Moong Chilla', emoji: '🥞', cal: 230, diets: ['Vegetarian', 'Vegan', 'Eggetarian', 'Non-Vegetarian', 'Jain'], cost: 'Low' },
    { name: 'Avocado Toast', emoji: '🥑', cal: 320, diets: ['Vegetarian', 'Vegan', 'Eggetarian', 'Non-Vegetarian', 'Keto'], cost: 'High' },
    { name: 'Masala Omelette', emoji: '🍳', cal: 290, diets: ['Eggetarian', 'Non-Vegetarian', 'Keto'], cost: 'Low' },
    { name: 'Greek Yogurt Parfait', emoji: '🍓', cal: 240, diets: ['Vegetarian', 'Eggetarian', 'Non-Vegetarian'], cost: 'Medium' },
    { name: 'Smoothie Bowl', emoji: '🥭', cal: 270, diets: ['Vegetarian', 'Vegan', 'Eggetarian', 'Non-Vegetarian'], cost: 'Medium' },
    { name: 'Paneer Bhurji Wrap', emoji: '🌯', cal: 340, diets: ['Vegetarian', 'Eggetarian', 'Non-Vegetarian', 'Keto'], cost: 'Medium' },
  ],
  lunch: [
    { name: 'Dal, Rice & Salad', emoji: '🍛', cal: 480, diets: ['Vegetarian', 'Vegan', 'Eggetarian', 'Non-Vegetarian', 'Jain'], cost: 'Low' },
    { name: 'Rajma Chawal', emoji: '🫘', cal: 520, diets: ['Vegetarian', 'Vegan', 'Eggetarian', 'Non-Vegetarian'], cost: 'Low' },
    { name: 'Paneer Wrap', emoji: '🌯', cal: 450, diets: ['Vegetarian', 'Eggetarian', 'Non-Vegetarian', 'Keto'], cost: 'Medium' },
    { name: 'Quinoa Veg Bowl', emoji: '🥗', cal: 420, diets: ['Vegetarian', 'Vegan', 'Eggetarian', 'Non-Vegetarian', 'Jain'], cost: 'High' },
    { name: 'Chicken Salad Bowl', emoji: '🍗', cal: 410, diets: ['Non-Vegetarian', 'Keto'], cost: 'Medium' },
    { name: 'Veg Pulao & Raita', emoji: '🍚', cal: 460, diets: ['Vegetarian', 'Eggetarian', 'Non-Vegetarian', 'Jain'], cost: 'Low' },
    { name: 'Chana Masala & Roti', emoji: '🫓', cal: 500, diets: ['Vegetarian', 'Vegan', 'Eggetarian', 'Non-Vegetarian'], cost: 'Low' },
    { name: 'Egg Curry & Rice', emoji: '🥚', cal: 510, diets: ['Eggetarian', 'Non-Vegetarian'], cost: 'Medium' },
    { name: 'Grilled Fish & Greens', emoji: '🐟', cal: 430, diets: ['Non-Vegetarian', 'Keto'], cost: 'High' },
  ],
  dinner: [
    { name: 'Quinoa Salad', emoji: '🥗', cal: 380, diets: ['Vegetarian', 'Vegan', 'Eggetarian', 'Non-Vegetarian', 'Jain'], cost: 'High' },
    { name: 'Grilled Veg Platter', emoji: '🍆', cal: 340, diets: ['Vegetarian', 'Vegan', 'Eggetarian', 'Non-Vegetarian', 'Keto', 'Jain'], cost: 'Medium' },
    { name: 'Palak Paneer & Roti', emoji: '🥬', cal: 450, diets: ['Vegetarian', 'Eggetarian', 'Non-Vegetarian', 'Keto'], cost: 'Medium' },
    { name: 'Lentil Soup & Toast', emoji: '🍲', cal: 330, diets: ['Vegetarian', 'Vegan', 'Eggetarian', 'Non-Vegetarian', 'Jain'], cost: 'Low' },
    { name: 'Khichdi & Kadhi', emoji: '🍚', cal: 420, diets: ['Vegetarian', 'Eggetarian', 'Non-Vegetarian', 'Jain'], cost: 'Low' },
    { name: 'Tandoori Chicken Plate', emoji: '🍗', cal: 440, diets: ['Non-Vegetarian', 'Keto'], cost: 'Medium' },
    { name: 'Stir-Fry Tofu Noodles', emoji: '🍜', cal: 400, diets: ['Vegetarian', 'Vegan', 'Eggetarian', 'Non-Vegetarian'], cost: 'Medium' },
    { name: 'Mushroom Garlic Rice', emoji: '🍄', cal: 390, diets: ['Vegetarian', 'Vegan', 'Eggetarian', 'Non-Vegetarian'], cost: 'Medium' },
    { name: 'Baked Salmon & Veg', emoji: '🐟', cal: 460, diets: ['Non-Vegetarian', 'Keto'], cost: 'High' },
  ],
};

export const WEEK_DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];



export const HELP_FAQ = [
  { q: 'How accurate is the food recognition?', a: 'Food Verse AI gives an estimate with a confidence score. Nutrition values vary with preparation and portion size, so treat them as a guide, not medical advice.' },
  { q: 'Can the freshness check guarantee food safety?', a: 'No. It is an AI-based prediction and may not be 100% accurate. When in doubt, throw it out.' },
  { q: 'Where is my data stored?', a: 'In this demo your profile and settings are stored only in your browser (localStorage). Nothing is uploaded to a server.' },
  { q: 'How do I change my daily calorie goal?', a: 'Open Profile & Settings → Health Goals and pick a goal, or use the Personalized Meal Planner controls.' },
];
