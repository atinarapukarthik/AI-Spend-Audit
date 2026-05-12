# AI Spend Audit

A B2B SaaS backend API that calculates AI tool overspending and generates personalized financial summaries.

## Overview

This service analyzes company AI tool subscriptions (Cursor, GitHub Copilot, Claude, ChatGPT) and identifies potential cost savings by recommending optimal plan tier transitions. It generates personalized 100-word financial summaries using NVIDIA NIM LLM.

## Tech Stack

- **Framework**: FastAPI
- **Database**: Supabase (PostgreSQL)
- **LLM**: NVIDIA NIM API (via localhost proxy)
- **Python**: 3.12+

## Project Structure

```
AI-Spend-Audit/
├── backend/
│   ├── main.py           # FastAPI application
│   ├── audit_engine.py   # Pricing & savings calculations
│   ├── requirements.txt   # Python dependencies
│   ├── .env.example      # Environment template
│   └── .gitignore        # Git ignore rules
├── supabase_schema.sql   # Database schema
├── .venv/                # Virtual environment
├── LICENSE
└── README.md
```

## Setup

### 1. Install Dependencies

```bash
cd backend
python -m venv ../.venv
source ../.venv/bin/activate  # Linux/Mac
../.venv/Scripts/activate     # Windows

pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cd backend
cp .env.example .env
```

Edit `.env` with your values:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key_here
PORT=8000
```

### 3. Setup Supabase Database

Run the schema in Supabase SQL Editor:

1. Go to your Supabase project
2. Navigate to **SQL Editor**
3. Paste the contents of `supabase_schema.sql`
4. Click **Run**

This creates:
- `leads` table - stores user emails and company info
- `audits` table - stores audit analysis records
- Required indexes and RLS policies

### 4. Run the Server

```bash
cd backend
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

## API Reference

### Health Check

```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "ai-spend-audit"
}
```

### Generate Audit

```
POST /api/v1/generate-audit
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "user@company.com",
  "company_name": "Acme Corp",
  "tools": [
    {
      "tool": "cursor",
      "plan": "business",
      "seats": 5
    },
    {
      "tool": "github_copilot",
      "plan": "team",
      "seats": 10
    }
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "audit_id": "uuid-string"
}
```

#### Supported Tools

| Tool | Key |
|------|-----|
| Cursor | `cursor` |
| GitHub Copilot | `github_copilot` |
| Claude | `claude` |
| ChatGPT | `chatgpt` |

#### Supported Plans

| Plan | Description |
|------|-------------|
| `hobby` | Free tier |
| `pro` | Individual professional plan |
| `team` | Team collaboration plan |
| `business` | Business plan (Cursor only) |
| `enterprise` | Enterprise/custom pricing |

## Savings Logic

The audit engine recommends downgrades that maintain value while reducing costs:

| Current Plan | Recommendation | Monthly Savings |
|--------------|----------------|-----------------|
| **Cursor Enterprise** | Business | $20/seat |
| **Cursor Business** | Pro | $20/seat |
| **GitHub Copilot Enterprise** | Team | $2/seat |
| **GitHub Copilot Team** | Pro | $9/seat |
| **GitHub Copilot Pro** | Free | $10/seat |
| **Claude Enterprise** | Team | Varies |
| **Claude Team** | Pro | $5/seat |
| **Claude Pro** | Free | $20/seat |
| **ChatGPT Enterprise** | Team | Varies |
| **ChatGPT Team** | Pro | $5/seat |
| **ChatGPT Pro** | Free | $20/seat |

## Development

### Run Tests

```bash
cd backend
pytest
```

### Code Formatting

```bash
ruff check .
ruff format .
```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Client App    │────▶│   FastAPI       │────▶│   Supabase      │
│   (Frontend)    │     │   Backend       │     │   Database      │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │   NVIDIA NIM    │
                         │   LLM Proxy     │
                         └─────────────────┘
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_KEY` | Yes | Supabase anon/public key |
| `PORT` | No | Server port (default: 8000) |

## License

See [LICENSE](LICENSE) file for details.
