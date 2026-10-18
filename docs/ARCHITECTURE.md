# FoodVerse AI — System Architecture

> Based on the live implementation as of 2026-10-18.  
> All descriptions reflect actual deployed code, not aspirational design.

---

## Overview

FoodVerse AI is a monorepo consisting of three top-level directories:

```
FoodVerse-AI/
├── backend/     FastAPI Python application
├── frontend/    React / Vite SPA
└── docs/        Architecture, testing, and audit documentation
```

---

## Backend Architecture

### Framework and Server

| Component | Technology |
|-----------|-----------|
| Web framework | FastAPI ≥ 0.111 |
| ASGI server | Uvicorn (with `--reload` in development) |
| File upload | `python-multipart` |
| Config | `python-dotenv` — reads `backend/.env` |

### Entry Point

`backend/app.py` (32 KB) declares all FastAPI routes, request/response models, CORS middleware, and application startup. It initialises the Gemini client once at module import and delegates to the service layer for all AI inference.

### Service Layer

Each AI feature has a dedicated service module. Services call Gemini via a shared internal helper and return typed Python dicts that FastAPI serialises to JSON.

| Module | Responsibility |
|--------|---------------|
| `image_processor.py` | OpenCV preprocessing: decode, normalize (Grayscale/RGBA→RGB), aspect-preserving resize, Laplacian sharpness, Rec.601 luminance, HSV colour, Sobel texture — returns `preprocessing_features` dict |
| `freshness_service.py` | Gemini Vision freshness assessment → `{status, label, certainty, food_item, safety_recommendations, disclaimer}` |
| `hygiene_service.py` | Video/image hygiene analysis — OpenCV frame extraction + Gemini Vision → compliance score, evidence, recommendations |
| `video_processor.py` | Configurable-interval OpenCV frame sampling with size limit, aspect-preserving resize, and `finally` temp-file cleanup |
| `cooking_service.py` | Gemini LLM recipe generation → structured recipe with steps, tips, food-safety reminders, nutrition tip |
| `meal_planner_service.py` | Gemini LLM daily / 7-day meal plan generation using user profile constraints |
| `nutrition_service.py` | Hierarchical ICMR-NIN IFCT 2017 + USDA FDC reference lookup → calories, protein, carbs, fat, fibre + deterministic 0-100 health score |
| `profile_service.py` | User profile CRUD backed by SQLite |

### Database

`database.py` manages a single SQLite file (`foodverse.db`). Tables are created with `CREATE TABLE IF NOT EXISTS` on module import — no manual migration is ever needed.

| Table | Contents |
|-------|----------|
| `activity_logs` | Every AI inference request (module, title, metadata JSON, timestamp) |
| `meal_plans` | Saved meal plans (plan type, JSON payload, timestamp) |
| `user_profiles` | User profile records (age, height, weight, goal, diet, allergies, etc.) |

### AI Engine — Google Gemini

All five inference modules use the `google-genai` SDK (`from google import genai`).

**Model cascade (quota failover):**
```
gemini-3.5-flash-lite → gemini-3.5-flash → gemini-3.7-flash → gemini-3.8-flash
```

The application tries the lightest model first and automatically retries on quota errors. Gemini Vision handles all visual tasks; Gemini LLM handles cooking and meal planning.

> **Important:** The TensorFlow MobileNetV2 model (`ml/`) was an early prototype. It is **not connected to any FastAPI endpoint**. All production inference goes through Gemini.

### API Routes Summary

```
GET  /api/health          — status, engine info, gemini_available flag
POST /api/predict         — food recognition + nutrition  (field: image)
POST /api/freshness       — freshness detection          (field: image)
POST /api/hygiene         — hygiene compliance           (field: image or video)
POST /api/cooking         — recipe generation            (JSON body)
GET  /api/profile         — get user profile
POST /api/profile         — create user profile
PUT  /api/profile         — update user profile
POST /api/meal-plan       — daily or weekly meal plan    (JSON body)
GET  /api/dashboard/stats — dashboard metrics
GET  /api/activities      — recent activity feed
```

### CORS

Configured in `app.py` to allow `http://localhost:5173` (Vite dev server). Must be updated to include the production domain before any public deployment.

---

## Frontend Architecture

### Framework and Tooling

| Component | Technology |
|-----------|-----------|
| UI library | React 18 |
| Build tool | Vite 5 |
| Language | JavaScript (ES modules) |
| Routing | React Router 6 |
| Charting | Recharts |
| Icons | Lucide React |
| PDF export | jsPDF (client-side) |
| Test runner | Vitest + Testing Library |

### Application Structure

```
frontend/src/
├── App.jsx                  Router, auth guard, layout wrapper
├── main.jsx                 ReactDOM.createRoot entry
├── pages/                   One file per route (10 pages)
│   ├── Landing.jsx
│   ├── Auth.jsx
│   ├── Dashboard.jsx
│   ├── FoodRecognition.jsx
│   ├── Freshness.jsx
│   ├── Hygiene.jsx
│   ├── Cooking.jsx
│   ├── MealPlanner.jsx
│   ├── Profile.jsx
│   └── NotFound.jsx
├── components/              Shared UI components
│   ├── AppLayout.jsx        Sidebar navigation shell
│   ├── ImageUploader.jsx    Drag-and-drop upload widget
│   ├── ProgressRing.jsx     SVG radial progress indicator
│   ├── FoodArt.jsx          Inline SVG food illustrations
│   └── landing/             Landing page section components
├── context/
│   ├── AuthContext.jsx      Demo authentication (localStorage)
│   ├── AppDataContext.jsx   Global app state (meals, activities, profile)
│   └── ToastContext.jsx     Toast notification system
├── hooks/
│   └── useImageUpload.js    Image file selection + preview state
├── data/
│   └── mock.js              Seed data for demo login and initial state
├── utils/
│   ├── analysis.js          All backend API call helpers (fetch wrappers)
│   ├── pdfGenerator.js      jsPDF PDF generation for all six modules
│   ├── helpers.js           Shared utility functions
│   └── validators.js        Form input validators
└── styles/
    ├── tokens.css            Design tokens (colours, radii, shadows, fonts)
    ├── base.css              Global resets and typography
    ├── components.css        Shared component styles
    ├── layout.css            App layout and navigation
    ├── pages.css             Page-specific styles
    └── landing.css           Landing page styles
```

### Routes

| Path | Page | Notes |
|------|------|-------|
| `/` | Landing | Public |
| `/login`, `/signup` | Auth | Demo login available |
| `/app` | Dashboard | Protected |
| `/app/food` | Food Recognition | Protected |
| `/app/freshness` | Freshness Detection | Protected |
| `/app/hygiene` | Hygiene Monitor | Protected |
| `/app/cooking` | Smart Kitchen | Protected |
| `/app/meal-planner` | Meal Planner | Protected |
| `/app/profile` | Profile | Protected |
| `*` | NotFound | Public |

### API Communication

`src/utils/analysis.js` wraps all `fetch` calls to `/api/*`. Vite's proxy configuration (`vite.config.js`) forwards these to `http://localhost:8000` during development — **no API URL is hardcoded in frontend source.**

### Data Persistence

- User session and preferences: `localStorage` (prefixed `fv_`)
- Inference history, meal plans, profiles: SQLite via backend API

---

## Data Flow — Food Recognition Example

```
User selects image
       │
       ▼
ImageUploader.jsx  →  analyzeFood() in analysis.js
       │
       ▼
POST /api/predict (multipart, field: image)
       │
       ▼
app.py → image_processor.py (OpenCV decode + preprocess)
       │
       ▼
Gemini Vision (gemini-3.5-flash-lite)
       │
       ▼
nutrition_service.py (ICMR-NIN / USDA lookup + health score)
       │
       ▼
JSON response → FoodRecognition.jsx renders result + PDF option
       │
       ▼
database.log_activity() → activity_logs table
```

---

## Security Notes

- `GEMINI_API_KEY` lives only in `backend/.env` — excluded from version control by `.gitignore`
- No API keys are present in any frontend source file
- Uploaded images and videos are processed in memory; video frames use a temp file with guaranteed `finally`-block cleanup
- SQLite database (`foodverse.db`) is excluded from version control

---

## Technology Gaps (Declared, Not Yet Integrated)

The following packages are declared in `requirements.txt` as Smart Bridge requirements but are not wired to active API endpoints:

| Technology | Status |
|-----------|--------|
| PyTorch + torchvision | Installed, not used in any route |
| HuggingFace Transformers | Installed, not used in any route |
| TensorFlow | Installed, not used in any route (`.keras` model removed) |
| Meta LLaMA | Not installed — requires separate model weights |
| `fpdf2` | Installed (server-side PDF); client-side jsPDF is the active PDF engine |

---

## Testing Strategy & Verification

### Backend Testing (204 Tests)
The backend test suite is organized into 5 logically grouped domain test modules in `backend/tests/`:

| Test Suite | Tests | Scope |
|---|---|---|
| `test_food_and_nutrition.py` | 24 | Food recognition, OpenCV decode/resize, /api/predict contract, ICMR-NIN/USDA lookup, portion scaling, 0–100 health scoring |
| `test_freshness_and_preprocessing.py` | 46 | OpenCV image preprocessing (sharpness, blur, exposure, HSV, texture, freshness cues) and freshness classification |
| `test_hygiene_and_cooking.py` | 38 | Video processing, hygiene observation parsing, compliance scoring, and recipe generation logic |
| `test_profile_and_meal_planner.py` | 44 | User profile validation, calorie targets, allergen/intolerance enforcement, and 1-day/7-day meal plan synthesis |
| `test_system_and_edge_cases.py` | 52 | Full-system API integration and cross-module edge cases (corrupt uploads, zero-byte files, extreme bounds, timeouts) |

**Execution:**
```powershell
cd backend
.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -t . -v
```

### Frontend Testing (26 Tests)
The frontend uses Vitest + @testing-library/react for component and integration testing:

| Test File | Tests | Scope |
|---|---|---|
| `src/test/app.test.jsx` | 13 | Full application integration: navigation, login, food recognition, cooking assistant, meal plan generation, profile edits |
| `src/test/foodRecognition.test.jsx` | 5 | Component-level testing of FoodRecognition: file drop, format validation, preview, and results display |
| `src/test/pdfGenerator.test.js` | 8 | jsPDF client-side generation verification for all 6 PDF report types |

**Execution:**
```powershell
cd frontend
npm test -- --run
```

