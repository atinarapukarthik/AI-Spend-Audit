"""
AI Spend Audit - FastAPI Backend
B2B SaaS tool that calculates AI tool overspending and generates personalized summaries.
"""

import os
import uuid
import smtplib
from typing import Any
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from supabase import create_client, Client
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

from audit_engine import calculate_savings

load_dotenv()

# Rate Limiter setup
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="AI Spend Audit API",
    description="Backend API for AI Spend Audit - Calculate overspending on AI tools",
    version="1.0.0",
)

# Add rate limiter to app state
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors."""
    return HTTPException(
        status_code=429,
        detail=f"Rate limit exceeded. Please try again later."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
@limiter.limit("5/minute")
async def generate_audit(request: Request, audit_request: AuditRequest) -> AuditResponse:
    """
    Generate an AI spend audit with savings analysis and LLM-powered summary.

    This endpoint:
    1. Accepts user email and list of AI tools with their current plans
    2. Calculates potential savings using the audit engine
    3. Generates a personalized 100-word financial summary using NVIDIA NIM LLM
    4. Upserts the lead into Supabase and creates an audit record
    5. Sends a transactional email to the user
    """
    try:
        input_data = [tool.model_dump() for tool in audit_request.tools]

        savings_result = calculate_savings(input_data)

        ai_summary = await generate_llm_summary(
            email=audit_request.email,
            company_name=audit_request.company_name,
            savings_data=savings_result,
        )

        lead_id = upsert_lead(
            email=audit_request.email,
            company_name=audit_request.company_name,
        )

        audit_id = create_audit(
            lead_id=lead_id,
            input_data=input_data,
            savings_data=savings_result,
            ai_summary=ai_summary,
        )

        # Send transactional email via Gmail SMTP (non-blocking)
        request_origin = request.headers.get("origin") or str(request.url)
        await send_confirmation_email(
            email=audit_request.email,
            audit_id=str(audit_id),
            company_name=audit_request.company_name,
            request_origin=request_origin,
        )

        return AuditResponse(status="success", audit_id=str(audit_id))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate audit: {str(e)}")


async def send_confirmation_email(
    email: str,
    audit_id: str,
    company_name: str | None = None,
    request_origin: str = "http://localhost:3000",
) -> None:
    """Send a confirmation email using Gmail SMTP."""
    try:
        gmail_address = os.getenv("GMAIL_ADDRESS")
        gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")

        if not gmail_address or not gmail_app_password:
            print("GMAIL_ADDRESS or GMAIL_APP_PASSWORD not set, skipping email")
            return

        # Determine if request is from local or production
        is_local = "localhost" in request_origin or "127.0.0.1" in request_origin
        
        if is_local:
            frontend_url = os.getenv("LOCAL_FRONTEND_URL", "http://localhost:3000")
        else:
            frontend_url = os.getenv("PRODUCTION_FRONTEND_URL", os.getenv("FRONTEND_URL", "http://localhost:3000"))
        
        audit_url = f"{frontend_url}/audit/{audit_id}"
        
        # Logo SVG as data URI for the circle
        logo_svg = '''<svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="18" cy="18" r="18" fill="#2563EB"/>
            <text x="18" y="23" text-anchor="middle" fill="white" font-size="16" font-weight="bold" font-family="Arial">C</text>
        </svg>'''

        company_display = company_name if company_name else "there"

        # Build HTML email body - premium styled template
        html_content = f"""
    <!DOCTYPE html>
    <html>
    <body style="background-color: #f4f4f5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; padding: 40px 0; margin: 0;">
        <div style="max-width: 500px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <div style="background-color: #09090b; padding: 30px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 600;">Credex AI Spend Audit</h1>
            </div>
            <div style="padding: 40px 30px;">
                <h2 style="margin-top: 0; color: #18181b; font-size: 20px;">Your audit is ready.</h2>
                <p style="color: #52525b; font-size: 16px; line-height: 1.5; margin-bottom: 30px;">
                    We've analyzed your current AI stack. Good news—we found potential optimizations that could lower your monthly burn rate.
                </p>
                <div style="text-align: center;">
                    <a href="{audit_url}" 
                       style="background-color: #10b981; color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block; font-size: 16px;">
                        View Your Dashboard &rarr;
                    </a>
                </div>
                <p style="color: #a1a1aa; font-size: 14px; line-height: 1.5; margin-top: 30px; border-top: 1px solid #e4e4e7; padding-top: 20px;">
                    If your savings are significant, a Credex optimization specialist will reach out shortly to help you capture them.
                </p>
            </div>
        </div>
    </body>
    </html>
        """

        # Build the email
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Your AI Spend Audit Results"
        msg["From"] = formataddr(("Credex Audit Team", gmail_address))
        msg["To"] = email

        # Attach HTML part
        html_part = MIMEText(html_content, "html")
        msg.attach(html_part)

        # Send via Gmail SMTP SSL on port 465
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_address, gmail_app_password)
            server.sendmail(gmail_address, email, msg.as_string())

        print(f"Email sent successfully to {email}")

    except Exception as e:
        # Log silently, don't crash the endpoint
        print(f"Failed to send confirmation email to {email}: {e}")


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

        user_prompt = f"""You are a financial advisor for startups. Write a concise, 
        personalized 100-word summary about AI tool spending optimization. 
        Use a professional, friendly tone. Be specific about the savings.

        Company: {company_text}
        Email: {email}

        Current spending analysis:
        {tools_text}

        Total potential monthly savings: ${total_savings}

        Write exactly 100 words summarizing the findings and actionable recommendations."""

        nvidia_api_key = os.getenv("NVIDIA_API_KEY")
        if not nvidia_api_key:
            raise ValueError("NVIDIA_API_KEY not set in environment")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                json={
                    "model": "deepseek-ai/deepseek-v4-flash",
                    "messages": [
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": 256,
                    "temperature": 0.7,
                },
                headers={
                    "Authorization": f"Bearer {nvidia_api_key}",
                    "Content-Type": "application/json",
                },
                timeout=180,
            )

            if response.status_code != 200:
                raise Exception(f"NVIDIA NIM API error: {response.status_code} - {response.text}")

            result = response.json()
            summary = result["choices"][0]["message"]["content"]

            words = summary.split()
            if len(words) > 100:
                summary = " ".join(words[:100])

            return summary

    except Exception as e:
        print(f"LLM generation failed: {e}")
        return f"AI Spend Audit complete. Your team can save ${total_savings} monthly by optimizing AI tool subscriptions. Review the detailed breakdown for specific recommendations."


def upsert_lead(email: str, company_name: str | None) -> uuid.UUID:
    """Upsert the lead into the leads table and return the lead_id."""
    response = supabase.table("leads").upsert(
        {"email": email, "company_name": company_name},
        on_conflict="email",
        returning="minimal",
    ).execute()

    fetch_response = supabase.table("leads").select("id").eq("email", email).execute()

    if not fetch_response.data or len(fetch_response.data) == 0:
        raise Exception("Failed to upsert lead")

    lead_id = fetch_response.data[0].get("id")
    if not lead_id:
        raise Exception("No lead_id returned")

    return uuid.UUID(lead_id)


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

    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)