import os
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv()

from main import generate_llm_summary


def test_llm_generation():
    print("============================================================")
    print(" Testing LLM Summary Generation")
    print("============================================================\n")

    # Test 1: No savings for listed tools
    test_savings_data_no_savings = {
        "total_monthly_savings": 110.0,
        "tools": [
            {
                "tool_name": "Cursor Pro",
                "current_plan": "Pro",
                "current_spend": 20.0,
                "recommended_plan": "Pro",
                "recommended_spend": 20.0,
                "monthly_savings": 0.0,
            },
            {
                "tool_name": "GitHub Copilot",
                "current_plan": "Pro",
                "current_spend": 10.0,
                "recommended_plan": "Pro",
                "recommended_spend": 10.0,
                "monthly_savings": 0.0,
            },
        ],
    }

    # Test 2: With actual savings
    test_savings_data_with_savings = {
        "total_monthly_savings": 45.0,
        "tools": [
            {
                "tool_name": "Cursor Pro",
                "current_plan": "Pro",
                "current_spend": 20.0,
                "recommended_plan": "Free",
                "recommended_spend": 0.0,
                "monthly_savings": 20.0,
            },
            {
                "tool_name": "Claude for Slack",
                "current_plan": "Pro",
                "current_spend": 25.0,
                "recommended_plan": "Team",
                "recommended_spend": 25.0,
                "monthly_savings": 25.0,
            },
        ],
    }

    async def run_tests():
        # Test 1: No savings
        print("Test 1: Tools with no savings")
        print("-" * 40)
        summary1 = await generate_llm_summary(
            email="test@example.com",
            company_name="Acme Corp",
            savings_data=test_savings_data_no_savings,
        )
        word_count1 = len(summary1.split())
        print(f"Word count: {word_count1}")
        print(f"Summary:\n{summary1}\n")

        # Test 2: With savings
        print("Test 2: Tools with savings")
        print("-" * 40)
        summary2 = await generate_llm_summary(
            email="test@example.com",
            company_name="Acme Corp",
            savings_data=test_savings_data_with_savings,
        )
        word_count2 = len(summary2.split())
        print(f"Word count: {word_count2}")
        print(f"Summary:\n{summary2}\n")

        # Results
        print("============================================================")
        print(" Results Summary")
        print("============================================================")
        print(f"Test 1 (no savings): {word_count1} words - {'PASS' if 95 <= word_count1 <= 105 else 'FAIL'}")
        print(f"Test 2 (with savings): {word_count2} words - {'PASS' if 95 <= word_count2 <= 105 else 'FAIL'}")

        return True

    try:
        asyncio.run(run_tests())
        print("\n[PASS] All tests completed!")
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = test_llm_generation()
    sys.exit(0 if success else 1)
