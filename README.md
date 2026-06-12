# ResumeTailor AI

AI-powered resume tailoring for every job application.

## Tech Stack

| Layer     | Technology                                           |
|-----------|------------------------------------------------------|
| Frontend  | Next.js 15, TypeScript, Tailwind CSS, Shadcn UI      |
| Backend   | FastAPI, Pydantic, Uvicorn                           |
| State     | TanStack Query                                       |
| Forms     | React Hook Form + Zod                                |

## Project Structure

```
ResumeTailor-AI/
├── frontend/          # Next.js 15 App Router application
│   └── src/
│       ├── app/       # App Router pages and layouts
│       ├── components/
│       │   └── ui/    # Shadcn UI components
│       ├── hooks/     # Custom React hooks
│       ├── lib/       # Shared utilities (cn, api client, etc.)
│       └── types/     # Shared TypeScript types
└── backend/           # FastAPI application
    ├── api/
    │   └── v1/        # Versioned route handlers
    ├── core/          # App configuration and settings
    ├── schemas/       # Pydantic request/response models
    ├── services/      # Business logic layer
    └── utils/         # Shared helpers
```

## Getting Started

### Prerequisites

- Node.js >= 20
- Python >= 3.11
- npm or pnpm

---

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Copy environment variables
cp .env.local.example .env.local

# Start development server (http://localhost:3000)
npm run dev
```

**Other commands:**

```bash
npm run build          # Production build
npm run lint           # ESLint check
npm run lint:fix       # ESLint auto-fix
npm run format         # Prettier format
npm run format:check   # Prettier dry-run
npm run type-check     # TypeScript check
```

---

### Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env

# Start development server (http://localhost:8000)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## API Reference

### Health Check

```
GET /api/v1/health
```

**Response:**

```json
{
  "status": "ok"
}
```

Interactive API docs are available at `http://localhost:8000/api/v1/docs`.

---

## Adding Shadcn UI Components

```bash
cd frontend
npx shadcn@latest add button
npx shadcn@latest add input
npx shadcn@latest add card
```

Components are placed in `src/components/ui/` automatically.

---

## Environment Variables

Copy `.env.example` at the root for an overview of all variables. Each service has its own env file:

| File                              | Purpose                        |
|-----------------------------------|--------------------------------|
| `frontend/.env.local.example`     | Frontend environment variables |
| `backend/.env.example`            | Backend environment variables  |
