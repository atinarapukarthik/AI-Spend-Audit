"""
AI Spend Audit Engine - Pricing calculations and savings analysis
"""

from typing import Any

PRICING_CONSTANTS: dict[str, dict[str, Any]] = {
    "cursor": {
        "name": "Cursor",
        "hobby": {"monthly": 0, "description": "Free tier with limited usage"},
        "pro": {"monthly": 20, "description": "Pro - $20/user/month"},
        "business": {"monthly": 40, "description": "Business - $40/user/month"},
        "enterprise": {"monthly": 60, "description": "Enterprise - $60/user/month"},
    },
    "github_copilot": {
        "name": "GitHub Copilot",
        "hobby": {"monthly": 0, "description": "Free for individuals (limited)"},
        "pro": {"monthly": 10, "description": "Pro - $10/user/month"},
        "team": {"monthly": 19, "description": "Team - $19/user/month"},
        "enterprise": {"monthly": 21, "description": "Enterprise - $21/user/month"},
    },
    "claude": {
        "name": "Claude (Anthropic)",
        "hobby": {"monthly": 0, "description": "Free tier with usage limits"},
        "pro": {"monthly": 20, "description": "Pro - $20/user/month"},
        "team": {"monthly": 25, "description": "Team - $25/user/month"},
        "enterprise": {"monthly": 0, "description": "Contact sales (custom pricing)"},
    },
    "chatgpt": {
        "name": "ChatGPT (OpenAI)",
        "hobby": {"monthly": 0, "description": "Free tier with limited GPT-4"},
        "pro": {"monthly": 20, "description": "Plus - $20/user/month"},
        "team": {"monthly": 25, "description": "Team - $25/user/month"},
        "enterprise": {"monthly": 0, "description": "Enterprise - Contact sales"},
    },
}

PLAN_RANKING: dict[str, int] = {
    "hobby": 0,
    "pro": 1,
    "team": 2,
    "business": 3,
    "enterprise": 4,
}


def calculate_savings(tools_list: list[dict]) -> dict:
    """
    Calculate current spend and potential savings for a list of AI tools.

    Args:
        tools_list: List of dicts with 'tool', 'plan', and 'seats' keys.
                    Example: [{"tool": "cursor", "plan": "business", "seats": 5}]

    Returns:
        Dictionary with per-tool breakdown and total monthly savings.
    """
    tool_breakdown = []
    total_monthly_savings = 0

    for tool_item in tools_list:
        tool_key = tool_item.get("tool", "").lower().strip()
        current_plan = tool_item.get("plan", "").lower().strip()
        seats = max(1, int(tool_item.get("seats", 1)))

        if tool_key not in PRICING_CONSTANTS:
            continue

        tool_pricing = PRICING_CONSTANTS[tool_key]
        current_price = tool_pricing.get(current_plan, {}).get("monthly", 0)
        current_spend = current_price * seats

        recommended_plan, recommended_price, savings = determine_optimal_plan(
            tool_key, current_plan, current_price, seats
        )

        tool_breakdown.append(
            {
                "tool": tool_key,
                "tool_name": tool_pricing["name"],
                "current_plan": current_plan,
                "current_spend": current_spend,
                "recommended_plan": recommended_plan,
                "recommended_spend": recommended_price * seats,
                "monthly_savings": savings,
            }
        )

        total_monthly_savings += savings

    return {
        "tools": tool_breakdown,
        "total_monthly_savings": total_monthly_savings,
    }


def determine_optimal_plan(
    tool_key: str, current_plan: str, current_price: float, seats: int
) -> tuple[str, int, int]:
    """
    Determine the optimal (most cost-effective) plan that still provides value.

    Returns:
        Tuple of (recommended_plan, recommended_price_per_seat, monthly_savings)
    """
    current_idx = PLAN_RANKING.get(current_plan, 1)
    current_spend = current_price * seats

    if tool_key == "cursor":
        if current_plan == "enterprise":
            return ("business", 40, (current_price - 40) * seats)
        elif current_plan == "business":
            return ("pro", 20, (current_price - 20) * seats)
        else:
            return (current_plan, current_price, 0)

    elif tool_key == "github_copilot":
        if current_plan == "enterprise":
            return ("team", 19, (current_price - 19) * seats)
        elif current_plan == "team":
            return ("pro", 10, (current_price - 10) * seats)
        elif current_plan == "pro":
            return ("hobby", 0, current_spend)
        else:
            return (current_plan, current_price, 0)

    elif tool_key == "claude":
        if current_plan == "enterprise":
            return ("team", 25, current_spend - (25 * seats))
        elif current_plan == "team":
            return ("pro", 20, (current_price - 20) * seats)
        elif current_plan == "pro":
            return ("hobby", 0, current_spend)
        else:
            return (current_plan, current_price, 0)

    elif tool_key == "chatgpt":
        if current_plan == "enterprise":
            return ("team", 25, current_spend - (25 * seats))
        elif current_plan == "team":
            return ("pro", 20, (current_price - 20) * seats)
        elif current_plan == "pro":
            return ("hobby", 0, current_spend)
        else:
            return (current_plan, current_price, 0)

    return (current_plan, current_price, 0)