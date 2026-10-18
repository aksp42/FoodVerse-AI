# FoodVerse AI — Backend Setup Guide
## Smart Bridge Milestone 1 (Activities 1.1 & 1.2)

---

## Quick Start

```powershell
# From the project root (C:\Users\HP\Desktop\SPS\food-verse-ai)
cd backend
python setup_env.py
```

This automated script creates the virtual environment, upgrades pip, installs all dependencies, validates imports, and sets up `.env`.

---

## Manual Setup (Step-by-Step)

### Prerequisites
- Python 3.9 or higher (Python 3.13.x installed — OK)
- 152 GB free disk space available (confirmed)
- Internet access for package downloads

### 1. Create Virtual Environment

```powershell
# PowerShell — run from backend/ directory
python -m venv venv
```

### 2. Activate Virtual Environment

**PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**CMD:**
```cmd
venv\Scripts\activate.bat
```

You should see `(venv)` at the start of your prompt.

### 3. Upgrade pip

```powershell
python -m pip install --upgrade pip setuptools wheel
```

### 4. Install All Dependencies

```powershell
pip install -r requirements.txt
```

> **Note:** PyTorch (~2 GB), OpenCV, and scikit-learn are large packages.
> Installation may take 5–15 minutes depending on internet speed.

### 5. Configure Environment Variables

```powershell
Copy-Item .env.example .env
```

Then open `.env` and set your `GEMINI_API_KEY`:
```
GEMINI_API_KEY=your_actual_key_here
```

Get a Gemini API key at: https://aistudio.google.com/app/apikey

### 6. Start the Backend

```powershell
uvicorn app:app --reload --port 8000
```

Backend will be available at: http://localhost:8000
API docs at: http://localhost:8000/docs

---

## Running Tests

Tests live in `backend/tests/`. Run from the `backend/` directory:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -t . -v
```

- `-s tests` — discover inside `tests/`
- `-t .` — sets top-level to `backend/` so `import app`, `import database`, etc. resolve correctly

**Expected result:** `Ran 204 tests in ~4s — OK`

---

## Deactivate Virtual Environment

```powershell
deactivate
```

---

## Package Summary

| Package | Purpose | Smart Bridge |
|---|---|---|
| `fastapi` | REST API framework | ✅ Required |
| `uvicorn` | ASGI server | ✅ Required |
| `python-multipart` | File upload handling | ✅ Required |
| `python-dotenv` | .env loading | ✅ Required |
| `google-genai` | Official Gemini AI SDK (app.py) | Active AI engine |
| `google-generativeai` | Legacy Gemini SDK compatibility | Fallback |
| `Pillow` | Image I/O in app.py | Used now |
| `numpy` | Array operations | Used now |
| `opencv-python-headless` | Image preprocessing | ✅ Required (integration pending) |
| `torch` + `torchvision` | Deep learning | ✅ Required (integration pending) |
| `transformers` | HuggingFace / LLaMA path | ✅ Required (integration pending) |
| `huggingface-hub` | Model hub access | Required by transformers |
| `pandas` | Data processing | ✅ Required |
| `scikit-learn` | ML utilities | ✅ Required |
| `requests` | HTTP client | Required |
| `fpdf2` | Server-side PDF generation | ✅ Required |
| `tensorflow` | Existing Keras model (.keras) | Existing asset |

## Intentionally Excluded Packages

| Package | Reason |
|---|---|
| `ultralytics` | YOLO not used — no object detection endpoint |
| `pytesseract` | OCR not implemented |
| `supabase` | Project uses SQLite (`database.py`), not Supabase |
| `openai` | Project uses Google Gemini, not OpenAI |
| `SpeechRecognition` / `pydub` | No audio pipeline implemented |
| `groq` | Not used |
| `jsPDF`, `recharts`, `react`, etc. | Frontend — managed by `package.json` |

---

## Smart Bridge Technology Gaps

These gaps are **documented** (not papered over). Actual integration is required in later activities:

| Technology | Status | Gap |
|---|---|---|
| OpenCV | Installed | Not yet imported in `app.py` — needs image preprocessing integration |
| PyTorch | Installed | Not yet used — needs model or inference code |
| Meta LLaMA | **Not installed** | Major gap — requires `llama-cpp-python` or Ollama + model weights |
| TF Keras model | Exists in `/ml/` | Not connected to `/api/predict` backend endpoint |

---

## Transformers / HuggingFace Compatibility Note

The **global** Python environment has a version conflict:
- `transformers 5.3.0` requires `huggingface-hub>=1.3.0,<2.0`
- But global `huggingface-hub==2.2.0` breaks `import transformers`

**This venv fixes this** by pinning `transformers>=4.40.0,<5.0.0` and `huggingface-hub>=0.23.0,<1.0.0` — compatible versions that work correctly together.

---

## Troubleshooting

**`Activate.ps1` blocked by execution policy:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**`torch` install is slow:** PyTorch CPU build is ~2 GB. This is expected.

**`tensorflow` import warning on Python 3.13:** TF officially supports up to Python 3.12. The installed build (2.21.0) works on 3.13 but is not officially tested. Use Python 3.11 or 3.12 if TF stability is critical.
