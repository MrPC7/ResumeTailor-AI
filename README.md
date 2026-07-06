# ResumeTailor AI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

ResumeTailor AI is a full-stack application for tailoring resumes to specific job descriptions. It parses uploaded resumes, analyzes job postings, evaluates ATS fit, generates improvement recommendations, and can produce a customized resume draft and cover letter.

## Features

- Upload and parse PDF or DOCX resumes
- Analyze a job description for role, seniority, and required skills
- Score resume relevance and produce ATS-oriented recommendations
- Generate a tailored resume version and optional cover letter
- Support Gemini as the primary LLM provider with Groq as a fallback

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS, shadcn/ui |
| Backend | FastAPI, Pydantic, Uvicorn |
| Parsing | PyMuPDF, python-docx |
| LLM | Google Gemini (primary), Groq (fallback) |

## Project Structure

```text
ResumeTailor-AI/
├── backend/          # FastAPI application
├── frontend/         # Next.js application
├── .env.example      # Root environment template
└── README.md
```

## Quick Start

### 1. Backend setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit the backend environment file and add your API keys:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
```

Start the API server:

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

- http://localhost:8000/api/v1/health
- http://localhost:8000/api/v1/docs

### 2. Frontend setup

```powershell
cd ../frontend
npm install
copy .env.local.example .env.local
npm run dev
```

Open http://localhost:3000 to use the app.

## Environment Variables

### Backend

The backend reads values from [backend/.env.example](backend/.env.example) and uses settings such as:

- `GEMINI_API_KEY`
- `GROQ_API_KEY`
- `GEMINI_MODEL`
- `GROQ_MODEL`
- `ALLOWED_ORIGINS`

### Frontend

The frontend expects:

- `NEXT_PUBLIC_API_URL=http://localhost:8000`

## Workflow

1. Upload a resume file.
2. Paste or provide a job description.
3. Review ATS analysis and recommendations.
4. Generate a tailored resume version.
5. Preview and export the final result.

## Notes

- The backend includes rate limiting and request size limits.
- If Gemini hits its quota, the app will fall back to Groq automatically.
- For local development, the frontend connects to the backend at port 8000 by default.

## Development

Run backend tests:

```powershell
cd backend
pytest
```

Build the frontend:

```powershell
cd frontend
npm run build
```
        ├── features/
        │   ├── workflow/
        │   │   ├── types/
        │   │   │   └── workflow.types.ts  # All shared TS types
        │   │   ├── store/
        │   │   │   └── workflow.store.ts  # Zustand store + dependency graph
        │   │   ├── services/             # API service modules
        │   │   │   ├── api.ts                    # Core HTTP client
        │   │   │   ├── parse-resume.service.ts   # File upload
        │   │   │   ├── extract-resume.service.ts # Structured extraction
        │   │   │   ├── analyze-jd.service.ts     # JD analysis
        │   │   │   ├── ats.service.ts            # ATS operations
        │   │   │   ├── customize-resume.service.ts # Optimization
        │   │   │   ├── export-resume.service.ts  # PDF/DOCX download
        │   │   │   └── cover-letter.service.ts   # Cover letter
        │   │   └── components/           # Step components
        │   │       ├── WorkflowStepper.tsx
        │   │       ├── StepUpload.tsx
        │   │       ├── StepJD.tsx
        │   │       ├── StepATS.tsx
        │   │       ├── StepRecommendations.tsx
        │   │       ├── StepPreview.tsx
        │   │       └── StepDownload.tsx
        │   └── resume-upload/
        │       └── schemas/
        │           └── upload-resume.schema.ts   # Zod file validation
        │
        └── lib/
            ├── utils.ts            # cn() class name utility
            └── toast.ts            # Event-driven toast system
```

---

## Local Setup

### Prerequisites

| Tool       | Version  | Required |
|------------|----------|----------|
| Node.js    | ≥ 20     | Yes      |
| Python     | ≥ 3.10   | Yes      |
| npm        | ≥ 9      | Yes      |
| pip        | latest   | Yes      |
| Gemini API Key | —   | Yes (primary LLM) |
| Groq API Key   | —   | No (fallback LLM) |

### Step 1 — Clone the Repository

```bash
git clone https://github.com/<your-username>/ResumeTailor-AI.git
cd ResumeTailor-AI
```

### Step 2 — Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
```

Edit `backend/.env` and add your API keys:

```env
GEMINI_API_KEY=your_actual_gemini_key
GROQ_API_KEY=your_actual_groq_key      # optional, for fallback
```

Start the backend server:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API is now running at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Step 3 — Frontend Setup

Open a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.local.example .env.local
```

The default `NEXT_PUBLIC_API_URL=http://localhost:8000` should work if the backend is on the same machine. Edit if your backend runs elsewhere.

Start the frontend dev server:

```bash
npm run dev
```

The app is now running at `http://localhost:3000`.

### Step 4 — Verify

1. Open `http://localhost:3000` in your browser
2. Backend health check: `curl http://localhost:8000/api/v1/health` → `{"status":"ok"}`
3. Upload a PDF/DOCX resume and test the full workflow

### Available Scripts

**Frontend:**

```bash
npm run dev            # Dev server with Turbopack (http://localhost:3000)
npm run build          # Production build
npm run start          # Start production server
npm run lint           # ESLint check
npm run lint:fix       # ESLint auto-fix
npm run format         # Prettier format all files
npm run format:check   # Prettier dry-run
npm run type-check     # TypeScript type check (no emit)
```

**Backend:**

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000    # Dev server with hot reload
uvicorn main:app --host 0.0.0.0 --port 8000              # Production server
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable                | Default                         | Description                                      |
|-------------------------|---------------------------------|--------------------------------------------------|
| `PROJECT_NAME`          | `ResumeTailor AI`               | Application name                                 |
| `VERSION`               | `0.1.0`                         | API version string                               |
| `API_V1_PREFIX`         | `/api/v1`                       | Versioned API route prefix                       |
| `ALLOWED_ORIGINS`       | `["http://localhost:3000"]`     | CORS allowed origins                             |
| `ALLOWED_METHODS`       | `["GET","POST","OPTIONS"]`      | CORS allowed methods                             |
| `ALLOWED_HEADERS`       | `["Content-Type"]`              | CORS allowed headers                             |
| `TEMP_UPLOAD_DIR`       | `./tmp/uploads`                 | Temporary file upload directory (cleaned on boot)|
| `MAX_UPLOAD_SIZE_BYTES` | `10485760` (10 MB)              | Maximum upload file size                         |
| `MAX_REQUEST_BODY_BYTES`| `2097152` (2 MB)                | Maximum JSON request body size                   |
| `RATE_LIMIT_LLM`        | `10/minute`                     | Per-IP rate limit for LLM endpoints              |
| `LOG_FORMAT`            | `json`                          | Log format: `json` or `text`                     |
| `GEMINI_API_KEY`        | *(empty)*                       | **Required.** Google Gemini API key              |
| `GEMINI_MODEL`          | `gemini-2.5-flash`              | Gemini model name                                |
| `GEMINI_MAX_RETRIES`    | `2`                             | Max retry attempts per LLM call                  |
| `LLM_TIMEOUT_SECONDS`   | `30`                            | LLM request timeout                              |
| `GROQ_API_KEY`          | *(empty)*                       | Groq API key (optional fallback)                 |
| `GROQ_MODEL`            | `llama-3.3-70b-versatile`       | Groq model name                                  |

### Frontend (`frontend/.env.local`)

| Variable              | Default                   | Description              |
|-----------------------|---------------------------|--------------------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000`   | Backend API base URL     |

---

## API Reference

### Endpoints

| Method | Path                         | Rate Limited | Description                              |
|--------|------------------------------|:------------:|------------------------------------------|
| GET    | `/api/v1/health`             | No           | Health check                             |
| POST   | `/api/parse-resume`          | No           | Upload PDF/DOCX → raw text               |
| POST   | `/api/extract-resume`        | Yes          | Raw text → structured resume JSON        |
| POST   | `/api/analyze-jd`            | Yes          | Job description → structured analysis    |
| POST   | `/api/ats/analyze`           | Yes          | Resume + JD → ATS evaluation scores      |
| POST   | `/api/ats/potential`         | No           | Predict max achievable ATS score         |
| POST   | `/api/ats/recommendations`   | No           | Generate improvement recommendations     |
| POST   | `/api/ats/compare`           | Yes          | Compare before/after ATS scores          |
| POST   | `/api/customize-resume`      | Yes          | Apply recommendations → optimized resume |
| POST   | `/api/export`                | No           | Structured resume → PDF/DOCX binary      |
| POST   | `/api/cover-letter`          | Yes          | Generate a tailored cover letter         |

### Health Check

```
GET /api/v1/health
```

```json
{
  "status": "ok"
}
```

Interactive API docs (Swagger UI) are available at `http://localhost:8000/docs`.

---

## Adding Shadcn UI Components

```bash
cd frontend
npx shadcn@latest add button
npx shadcn@latest add input
npx shadcn@latest add card
```

Components are placed in `src/components/ui/` automatically. Configuration lives in `components.json`.

---

## License

MIT © [Pranshu Chaurasia](https://pranshuchaurasia.dev)
