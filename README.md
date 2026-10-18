# FoodVerse AI

> **AI-powered food intelligence platform** — Gemini Vision + FastAPI + React

FoodVerse AI is a full-stack application that uses Google Gemini multimodal vision and language models to deliver six AI-powered food features: food recognition, freshness detection, restaurant hygiene monitoring, smart cooking guidance, personalized meal planning, and a nutritional dashboard.

---

## Features

| Module | Description |
|--------|-------------|
| 🍛 **Food Recognition** | Gemini Vision identifies food from photos and estimates nutrition (ICMR-NIN / USDA reference data) |
| 🥦 **Freshness Detection** | Visual freshness assessment with four confidence levels and food-safety guidance |
| 🏥 **Hygiene Monitoring** | Video or image analysis of restaurant/kitchen environments with compliance scoring |
| 👨‍🍳 **Smart Kitchen** | Ingredient-aware recipe generation with step-by-step cooking guidance |
| 📅 **Meal Planner** | Personalized daily and 7-day plans from saved user profile (goal, diet, allergies, budget) |
| 📊 **Dashboard** | Calorie history, macro splits, activity feed, and PDF export for all modules |

---

## Architecture

```
FoodVerse-AI/
├── backend/          FastAPI + Gemini AI services + SQLite
├── frontend/         React 18 + Vite 5 + Recharts
└── docs/             Architecture, testing, and audit documentation
```

**Primary AI engine:** Google Gemini Vision / LLM (`gemini-3.5-flash-lite` with automatic quota failover to `3.5-flash → 3.7-flash → 3.8-flash`)  
**Database:** SQLite via `database.py` (auto-initialises on first start)  
**Image processing:** OpenCV headless (preprocessing pipeline) + Pillow  
**PDF generation:** jsPDF (client-side, frontend)

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for full system design.

---

## Prerequisites

| Tool | Version | Required for |
|------|---------|-------------|
| Python | 3.9 – 3.13 | Backend |
| pip / venv | bundled with Python | Backend |
| Node.js | 18 + | Frontend |
| npm | 9 + | Frontend |
| Google Gemini API key | — | All AI features |

Get a free Gemini API key at <https://aistudio.google.com/app/apikey>.

---

## Quick Start

### 1 — Clone and enter the repo
```powershell
git clone <repo-url>
cd FoodVerse-AI
```

### 2 — Backend setup
```powershell
cd backend

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1          # PowerShell
# source venv/bin/activate           # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
Copy-Item .env.example .env
# Open .env and set GEMINI_API_KEY=your_key_here
```

> **Note:** PyTorch (~2 GB) and TensorFlow are listed in `requirements.txt` as declared Smart Bridge dependencies. They are installed but not actively wired to the FastAPI endpoints (Gemini Vision is the live inference engine). Installation takes 5–15 minutes depending on internet speed.

### 3 — Start the backend
```powershell
# From backend/
.\venv\Scripts\uvicorn.exe app:app --reload --port 8000
```

Backend available at: `http://localhost:8000`  
Interactive API docs at: `http://localhost:8000/docs`

### 4 — Frontend setup
```powershell
cd frontend
npm install
```

### 5 — Start the frontend
```powershell
# From frontend/
npm run dev
```

Frontend available at: `http://localhost:5173`  
All `/api/*` requests are automatically proxied to `http://localhost:8000` by Vite.

**Both backend and frontend must be running simultaneously for AI features to work.**

### Demo login
| Email | Password |
|-------|----------|
| `akanksha@example.com` | `FoodVerse1` |

Or click **Continue with demo account** on the login page.

---

## Configuration

### `backend/.env`
```
GEMINI_API_KEY=your_gemini_api_key_here
PORT=8000
```

Copy from `backend/.env.example`. Never commit the real `.env` file — it is excluded by `.gitignore`.

---

## Running Tests

### Backend (204 tests across 5 consolidated suites)
```powershell
cd backend
.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -t . -v
```

### Frontend (26 tests across 3 suites)
```powershell
cd frontend
npm test -- --run
```

### Frontend production build
```powershell
cd frontend
npm run build
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for full test architecture and coverage.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Service status and AI engine info |
| `POST` | `/api/predict` | Food recognition + nutrition (field: `image`) |
| `POST` | `/api/freshness` | Freshness detection (field: `image`) |
| `POST` | `/api/hygiene` | Hygiene / compliance analysis (field: `image`, video also accepted) |
| `POST` | `/api/cooking` | Recipe generation from ingredients / context |
| `GET` | `/api/profile` | Retrieve user profile |
| `POST` | `/api/profile` | Create user profile |
| `PUT` | `/api/profile` | Update user profile |
| `POST` | `/api/meal-plan` | Generate daily or weekly meal plan |
| `GET` | `/api/dashboard/stats` | Dashboard metrics |
| `GET` | `/api/activities` | Recent activity feed |

---

## Known Limitations

- **Gemini inference estimates** are informational and not medical or dietary advice.
- **Visual analysis** cannot guarantee food safety — always follow local food-safety standards.
- **PyTorch / HuggingFace Transformers / TensorFlow** are installed as Smart Bridge declared requirements but are not wired to active API endpoints (Gemini Vision is the live engine).
- **CORS** is configured for `localhost:5173` — update `allow_origins` in `backend/app.py` before any non-local deployment.
- **SQLite** is suitable for local development and demo; replace with PostgreSQL or similar for production multi-user deployment.

---

## Project Structure

```
FoodVerse-AI/
│
├── README.md                      Project landing page & guide
├── .gitignore                     Comprehensive root ignore
│
├── backend/
│   ├── app.py                     FastAPI entry point (all routes)
│   ├── database.py                SQLite schema + persistence
│   ├── image_processor.py         OpenCV preprocessing pipeline
│   ├── video_processor.py         OpenCV video frame extraction
│   ├── freshness_service.py       Gemini freshness inference
│   ├── hygiene_service.py         Gemini hygiene + compliance scoring
│   ├── cooking_service.py         Gemini recipe generation
│   ├── meal_planner_service.py    Gemini meal plan generation
│   ├── nutrition_service.py       ICMR-NIN / USDA nutrition reference
│   ├── profile_service.py         User profile CRUD
│   ├── requirements.txt           Backend dependencies
│   ├── .env.example               Environment template
│   ├── SETUP.md                   Backend setup guide
│   ├── setup_env.py               Automated venv + install script
│   └── tests/                     5 consolidated test suites (204 tests)
│       ├── __init__.py
│       ├── test_food_and_nutrition.py
│       ├── test_freshness_and_preprocessing.py
│       ├── test_hygiene_and_cooking.py
│       ├── test_profile_and_meal_planner.py
│       └── test_system_and_edge_cases.py
│
├── frontend/
│   ├── package.json               Frontend dependencies
│   ├── package-lock.json
│   ├── vite.config.js             Vite dev server & API proxy
│   ├── index.html                 HTML entry
│   ├── public/                    Static assets
│   └── src/                       React application source
│       ├── pages/                 10 page components
│       ├── components/            Shared UI & landing components
│       ├── context/               React context providers
│       ├── hooks/                 Custom React hooks
│       ├── styles/                CSS design tokens & page styles
│       ├── utils/                 API helpers & PDF generator
│       ├── data/mock.js           UI constants & template fallbacks
│       └── test/                  Vitest test suites (26 tests)
│
└── docs/
    └── ARCHITECTURE.md            System & testing architecture
```

---

## License

See `LICENSE` for terms. (Add before publishing.)

---

*Built by **Akanksha Singh** · FoodVerse AI · Smart Bridge Capstone Project*
