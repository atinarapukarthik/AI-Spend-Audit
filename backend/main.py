"""
AI Spend Audit - FastAPI Backend
B2B SaaS tool that calculates AI tool overspending and generates personalized summaries.
"""

import os
import uuid
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from openai import OpenAI
from pydantic import BaseModel, Field
from supabase import create_client, Client

from audit_engine import calculate_savings

load_dotenv()

app = FastAPI(
    title="AI Spend Audit API",
    description="Backend API for AI Spend Audit - Calculate overspending on AI tools",
    version="1.0.0",
)

from urllib.parse import urlparse

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")

parsed = urlparse(SUPABASE_URL)
if not all([parsed.scheme, parsed.netloc]) or parsed.scheme != "https":
    raise ValueError(
        f"Invalid SUPABASE_URL: '{SUPABASE_URL}'. "
        "Must be a valid HTTPS URL (e.g., https://your-project.supabase.co)"
    )

if not SUPABASE_KEY.startswith("eyJ"):
    raise ValueError(
        "Invalid SUPABASE_KEY format. It should start with 'eyJ' (JWT token)"
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

openai_client = OpenAI(
    base_url="http://localhost:8082/v1",
    api_key="free",
)


class ToolInput(BaseModel):
    tool: str = Field(..., description="AI tool name (e.g., cursor, github_copilot, claude, chatgpt)")
    plan: str = Field(..., description="Current plan tier (hobby, pro, team, business, enterprise)")
    seats: int = Field(default=1, ge=1, description="Number of seats/users")


class AuditRequest(BaseModel):
    email: str = Field(..., description="User's email address")
    company_name: str | None = Field(None, description="Company name (optional)")
    tools: list[ToolInput] = Field(..., min_length=1, description="List of AI tools to analyze")


class AuditResponse(BaseModel):
    status: str
    audit_id: str


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "ai-spend-audit"}


@app.post("/api/v1/generate-audit", response_model=AuditResponse)
async def generate_audit(request: AuditRequest) -> AuditResponse:
    """
    Generate an AI spend audit with savings analysis and LLM-powered summary.

    This endpoint:
    1. Accepts user email and list of AI tools with their current plans
    2. Calculates potential savings using the audit engine
    3. Generates a personalized 100-word financial summary using NVIDIA NIM LLM
    4. Upserts the lead into Supabase and creates an audit record
    """
    try:
        input_data = [tool.model_dump() for tool in request.tools]

        savings_result = calculate_savings(input_data)

        ai_summary = await generate_llm_summary(
            email=request.email,
            company_name=request.company_name,
            savings_data=savings_result,
        )

        lead_id = upsert_lead(
            email=request.email,
            company_name=request.company_name,
        )

        audit_id = create_audit(
            lead_id=lead_id,
            input_data=input_data,
            savings_data=savings_result,
            ai_summary=ai_summary,
        )

        return AuditResponse(status="success", audit_id=str(audit_id))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate audit: {str(e)}")


async def generate_llm_summary(
    email: str,
    company_name: str | None,
    savings_data: dict[str, Any],
) -> str:
    """Generate a personalized 100-word financial summary using NVIDIA NIM LLM."""
    try:
        total_savings = savings_data.get("total_monthly_savings", 0)
        tools = savings_data.get("tools", [])

        tool_details = []
        for tool in tools:
            tool_details.append(
                f"- {tool['tool_name']}: {tool['current_plan']} plan, "
                f"currently spending ${tool['current_spend']}/month, "
                f"can save ${tool['monthly_savings']}/month by switching to {tool['recommended_plan']}"
            )

        tools_text = "\n".join(tool_details)
        company_text = company_name if company_name else "your company"

        system_prompt = f"""You are a financial advisor for startups. Write a concise, 
personalized 100-word summary about AI tool spending optimization. 
Use a professional, friendly tone. Be specific about the savings.

Company: {company_text}
Email: {email}

Current spending analysis:
{tools_text}

Total potential monthly savings: ${total_savings}

Write exactly 100 words summarizing the findings and actionable recommendations."""

        response = openai_client.chat.completions.create(
            model="meta/llama3-70b-instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Generate the summary."},
            ],
            temperature=0.7,
            max_tokens=200,
        )

        summary = response.choices[0].message.content.strip()

        words = summary.split()
        if len(words) > 100:
            summary = " ".join(words[:100])

        return summary

    except Exception as e:
        print(f"LLM generation failed: {e}")
        return f"AI Spend Audit complete. Your team can save ${total_savings} monthly by optimizing AI tool subscriptions. Review the detailed breakdown for specific recommendations."


def upsert_lead(email: str, company_name: str | None) -> uuid.UUID:
    """Upsert the lead into the leads table and return the lead_id."""
    try:
        response = supabase.table("leads").upsert(
            {"email": email, "company_name": company_name},
            on_conflict="email",
            returning="id",
        ).execute()

        if not response.data or len(response.data) == 0:
            raise ValueError("Failed to upsert lead")

        lead_id = response.data[0].get("id")
        if not lead_id:
            raise ValueError("No lead_id returned from upsert")

        return uuid.UUID(lead_id)

    except Exception as e:
        raise Exception(f"Database error (leads): {str(e)}")


def create_audit(
    lead_id: uuid.UUID,
    input_data: list[dict],
    savings_data: dict[str, Any],
    ai_summary: str,
) -> uuid.UUID:
    """Insert a new audit record into the audits table."""
    try:
        audit_id = uuid.uuid4()

        supabase.table("audits").insert(
            {
                "id": str(audit_id),
                "lead_id": str(lead_id),
                "input_data": input_data,
                "savings_data": savings_data,
                "ai_summary": ai_summary,
            }
        ).execute()

        return audit_id

    except Exception as e:
        raise Exception(f"Database error (audits): {str(e)}")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)