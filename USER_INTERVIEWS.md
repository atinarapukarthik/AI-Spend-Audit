# User Interviews

**Goal:** Understand what makes technical users trust an automated AI spend audit tool.
**Question asked:** "If an app told you that you were overpaying for your AI tools, what would make you trust its math?"

### Interview 1
* **Initials/Role:** J.S. (Senior Frontend Developer)
* **Quote:** *"I wouldn't trust it if it asked for my email before showing me the calculations. I hate when SaaS tools hold the results hostage."*
* **Takeaway:** This validated my choice to show the shareable dashboard results immediately. It builds goodwill and proves the tool actually works before we attempt to capture the lead.

### Interview 2
* **Initials/Role:** M.T. (Engineering Manager)
* **Quote:** *"I'd need to see exactly which tier it thinks I should downgrade to. If it just gives a generic 'you can save $500', I'll assume it's a lead-gen scam."*
* **Takeaway:** This confirmed the absolute need for the "Tool-by-Tool Breakdown" section on the results page. Showing the explicit transition (e.g., `pro → hobby`) proves the math is based on actual vendor pricing.

### Interview 3
* **Initials/Role:** P.D. (Freelance Full-Stack Developer)
* **Quote:** *"If the tool doesn't account for the fact that Claude Team has a 5-seat minimum, I'd know it's fake. The edge cases matter."*
* **Takeaway:** This highlighted the importance of hardcoding specific vendor constraints into the backend `audit_engine.py`. By handling seat minimums correctly, the tool builds instant credibility with technical founders.