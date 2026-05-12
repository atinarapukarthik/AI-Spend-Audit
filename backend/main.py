"""
AI Spend Audit - FastAPI Backend
B2B SaaS tool that calculates AI tool overspending and generates personalized summaries.
"""

import os
import uuid
import json
import smtplib
from typing import Any
from urllib.parse import urlparse

from dotenv import load_dotenv, find_dotenv
from pathlib import Path
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from supabase import create_client, Client
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from google import genai

from audit_engine import calculate_savings

load_dotenv(Path(__file__).parent / ".env")

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

try:
    supabase.table("blueprints").select("id").limit(1).execute()
except Exception:
    print("WARNING: 'blueprints' table does not exist. Run:")
    print("  CREATE TABLE blueprints (")
    print("    id UUID PRIMARY KEY,")
    print("    audit_id UUID NOT NULL,")
    print("    content TEXT NOT NULL,")
    print("    created_at TIMESTAMPTZ DEFAULT NOW()")
    print("  );")


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


class BlueprintRequest(BaseModel):
    email: str = Field(..., description="Recipient email address")
    audit_id: str = Field(..., description="Audit ID to generate blueprint for")


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
    3. Generates a personalized 100-word financial summary using Gemini AI
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
        # Email bypass - set SKIP_EMAIL=true in .env to disable
        skip_email = os.getenv("SKIP_EMAIL", "false").lower() == "true"
        if not skip_email:
            request_origin = request.headers.get("origin") or str(request.url)
            await send_confirmation_email(
                email=audit_request.email,
                audit_id=str(audit_id),
                company_name=audit_request.company_name,
                request_origin=request_origin,
            )
        else:
            print("Email sending bypassed (SKIP_EMAIL=true)")

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

        print(f"[DEBUG] GMAIL_ADDRESS: {gmail_address}")
        print(f"[DEBUG] GMAIL_APP_PASSWORD: {gmail_app_password[:4] if gmail_app_password else None}****")

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


@app.post("/api/v1/generate-blueprint")
async def generate_blueprint(request: Request, blueprint_request: BlueprintRequest) -> dict[str, str]:
    """Generate a full Tactical Resource Memorandum, save to DB, and share the link."""
    try:
        gmail_address = os.getenv("GMAIL_ADDRESS")
        gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")
        if not gmail_address or not gmail_app_password:
            raise HTTPException(status_code=500, detail="Email not configured")

        audit_response = supabase.table("audits").select("*").eq("id", blueprint_request.audit_id).single().execute()
        if not audit_response.data:
            raise HTTPException(status_code=404, detail="Audit not found")

        audit_data = audit_response.data
        savings_data = audit_data.get("savings_data", {})
        tools = savings_data.get("tools", [])

        company_name = None
        lead_id = audit_data.get("lead_id")
        if lead_id:
            lead_resp = supabase.table("leads").select("company_name").eq("id", lead_id).single().execute()
            if lead_resp.data:
                company_name = lead_resp.data.get("company_name")

        total_savings = savings_data.get("total_monthly_savings", 0)

        blueprint_path = Path(__file__).parent.parent / "BLUEPRINT_REFERENCE.md"
        blueprint_directives = ""
        if blueprint_path.exists():
            blueprint_directives = blueprint_path.read_text()

        blueprint_content = ""
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if gemini_api_key:
            tools_json = json.dumps([{
                "tool": t["tool_name"],
                "plan": t["current_plan"],
                "current_spend": t["current_spend"],
                "recommended_plan": t["recommended_plan"],
                "recommended_spend": t["recommended_spend"],
                "savings": t["monthly_savings"],
            } for t in tools], indent=2)

            org_name = company_name or "anonymous organisation"
            system_prompt = f"""{blueprint_directives}

You are issuing a Tactical Resource Memorandum for {org_name}.

Additional Directives:
- Refer to the organisation's budget as 'capital liquidity'.
- Refer to each AI tool as an 'informational asset' or 'variable'.
- Analyse the math as a data puzzle to be solved — identify friction points, optimisable variables, and strategic yield.
- Structure: Situation, Analysis, Recommendation, Projected Outcome."""

            user_prompt = f"""Analyse this AI stack data for {org_name}:
{tools_json}

Total monthly burn: ${sum(t['current_spend'] for t in tools)}
Optimised burn: ${sum(t['recommended_spend'] for t in tools)}
Savings identified: ${total_savings}/mo

Task: Generate a complete Tactical Resource Memorandum. If savings are low, explain the stable equilibrium. If savings are high, identify primary friction points and command immediate action."""

            models_to_try = [
                "gemini-2.5-flash",
                "gemini-2.0-flash",
                "gemini-flash-latest",
                "gemini-2.0-flash-lite",
            ]

            for model_name in models_to_try:
                try:
                    print(f"Generating blueprint with {model_name}")
                    client = genai.Client(api_key=gemini_api_key)
                    response = client.models.generate_content(
                        model=model_name,
                        contents=user_prompt,
                        config={"system_instruction": system_prompt},
                    )
                    blueprint_content = response.text.strip()
                    if blueprint_content:
                        print("Blueprint generated")
                        break
                except Exception as e:
                    error_str = str(e)
                    if "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                        print(f"{model_name} quota exceeded, trying next")
                        continue
                    elif "API_KEY" in error_str or "Invalid" in error_str:
                        print(f"Invalid API key: {e}")
                        break
                    else:
                        print(f"{model_name} error: {e}")
                        continue

        if not blueprint_content:
            blueprint_content = _get_fallback_summary(total_savings, company_name)

        blueprint_id = uuid.uuid4()
        try:
            supabase.table("blueprints").insert({
                "id": str(blueprint_id),
                "audit_id": blueprint_request.audit_id,
                "content": blueprint_content,
            }).execute()
        except Exception as db_err:
            print(f"Blueprint DB insert failed (table may not exist): {db_err}")
            raise HTTPException(status_code=500, detail=f"Blueprint generated but could not be saved. Create the 'blueprints' table in Supabase SQL Editor: CREATE TABLE blueprints (id UUID PRIMARY KEY, audit_id UUID NOT NULL, content TEXT NOT NULL, created_at TIMESTAMPTZ DEFAULT NOW());")

        is_local = "localhost" in str(request.url) or "127.0.0.1" in str(request.url)
        frontend_url = (
            os.getenv("LOCAL_FRONTEND_URL", "http://localhost:3000") if is_local
            else os.getenv("PRODUCTION_FRONTEND_URL", os.getenv("FRONTEND_URL", "http://localhost:3000"))
        )

        blueprint_url = f"{frontend_url}/blueprint/{blueprint_id}"

        html_content = f"""
    <!DOCTYPE html>
    <html>
    <body style="background-color: #f4f4f5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; padding: 40px 0; margin: 0;">
        <div style="max-width: 500px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <div style="background-color: #09090b; padding: 30px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 600;">Tactical Resource Memorandum</h1>
            </div>
            <div style="padding: 40px 30px;">
                <h2 style="margin-top: 0; color: #18181b; font-size: 20px;">Strategic analysis complete.</h2>
                <p style="color: #52525b; font-size: 16px; line-height: 1.5; margin-bottom: 30px;">
                    A full expenditure breakdown has been compiled. Review the detailed assessment and recommended optimisations for your AI tool stack.
                </p>
                <div style="text-align: center;">
                    <a href="{blueprint_url}" 
                       style="background-color: #10b981; color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block; font-size: 16px;">
                        View Tactical Memorandum &rarr;
                    </a>
                </div>
                <p style="color: #a1a1aa; font-size: 14px; line-height: 1.5; margin-top: 30px; border-top: 1px solid #e4e4e7; padding-top: 20px;">
                    No action required at this time. Further recommendations will be issued if optimisation opportunities arise.
                </p>
            </div>
        </div>
    </body>
    </html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Tactical Resource Memorandum — AI Spend Audit"
        msg["From"] = formataddr(("Credex Strategic", gmail_address))
        msg["To"] = blueprint_request.email
        html_part = MIMEText(html_content, "html")
        msg.attach(html_part)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_address, gmail_app_password)
            server.sendmail(gmail_address, blueprint_request.email, msg.as_string())

        print(f"Blueprint {blueprint_id} dispatched to {blueprint_request.email}")

        return {"status": "dispatched", "blueprint_id": str(blueprint_id)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate blueprint: {str(e)}")


async def generate_llm_summary(
    email: str,
    company_name: str | None,
    savings_data: dict[str, Any],
) -> str:
    """Generate a personalized 100-word financial summary using Gemini AI."""
    total_savings = savings_data.get("total_monthly_savings", 0)
    tools = savings_data.get("tools", [])

    tool_details = []
    for tool in tools:
        tool_details.append(
            f"- {tool['tool_name']}: {tool['current_plan']} plan, "
            f"currently spending ${tool['current_spend']}/month, "
            f"can save ${tool['monthly_savings']}/month by switching to {tool['recommended_plan']}"
        )

    tools_text = "\n".join(tool_details) if tool_details else "No tools analyzed"

    tools_json = json.dumps([{
        "tool": t["tool_name"],
        "plan": t["current_plan"],
        "current_spend": t["current_spend"],
        "recommended_plan": t["recommended_plan"],
        "recommended_spend": t["recommended_spend"],
        "savings": t["monthly_savings"],
    } for t in tools], indent=2)

    system_prompt = """You are an optimized utilitarian strategist. Your objective is to issue a 'Tactical Resource Memorandum'.

Operational Directives:

Tone: Absolute detachment and logical instrumentalism.

Style: Use quantitative language. Refer to the user's budget as 'capital liquidity' and their tools as 'informational assets' or 'variables'.

Philosophy: Do not offer 'help'; offer 'optimization'.

Constraint: No conversational pleasantries. Always say less than necessary."""

    user_prompt = f"""Analyze this AI stack data: {tools_json}.
Task: Generate a 150-word Tactical Memorandum. If savings are low, explain why the current configuration is a stable equilibrium. If savings are high, identify the primary friction points and command immediate optimization."""

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print("GEMINI_API_KEY not set, using fallback")
        return _get_fallback_summary(total_savings, company_name)

    models_to_try = [
        ("gemini-2.5-flash", "Gemini 2.5 Flash"),
        ("gemini-2.0-flash", "Gemini 2.0 Flash"),
        ("gemini-flash-latest", "Gemini Flash Latest"),
        ("gemini-2.0-flash-lite", "Gemini 2.0 Flash Lite"),
    ]

    for model_name, model_label in models_to_try:
        try:
            print(f"Calling {model_label} API...")
            client = genai.Client(api_key=gemini_api_key)
            response = client.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config={
                    "system_instruction": system_prompt,
                },
            )
            summary = response.text.strip()
            words = summary.split()
            if len(words) > 100:
                summary = " ".join(words[:100])
            elif len(words) < 80:
                summary += " (Note: Summary generated at ~" + str(len(words)) + " words)"
            print(f"AI summary generated successfully with {model_label}")
            return summary
        except Exception as e:
            error_str = str(e)
            if "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                print(f"{model_label} quota exceeded, trying next model...")
                continue
            elif "API_KEY" in error_str or "Invalid" in error_str:
                print(f"Invalid API key: {e}")
                return _get_fallback_summary(total_savings, company_name)
            else:
                print(f"{model_label} error: {e}")
                continue

    print("All Gemini models failed, using fallback")
    return _get_fallback_summary(total_savings, company_name)


def _get_fallback_summary(total_savings: float, company_name: str | None) -> str:
    """Generate a fallback summary when LLM is unavailable."""
    if total_savings > 500:
        return f"Tactical Resource Memorandum. Analysis of {company_name or 'anonymous organisation'} AI stack reveals capital liquidity leakage of ${total_savings:,.0f}/mo. Primary friction point: over-provisioned enterprise-tier subscriptions. Command immediate downgrade of informational assets to recommended tiers. Projected strategic yield: ${total_savings:,.0f}/mo recovered."
    elif total_savings > 100:
        return f"Tactical Resource Memorandum. Assessment of {company_name or 'anonymous organisation'} AI tool variables identifies optimisation surface of ${total_savings:,.0f}/mo. Current configuration has moderate friction. Recommended action: adjust plan tiers per detailed breakdown. Expected yield: ${total_savings:,.0f}/mo."
    else:
        return f"Tactical Resource Memorandum. Examination of {company_name or 'anonymous organisation'} AI stack indicates stable equilibrium. Current variable configuration operates at near-optimal capital efficiency. No immediate optimisation action required. Savings potential: ${total_savings:,.0f}/mo."


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
