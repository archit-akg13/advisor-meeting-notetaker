"""Format extracted meeting data into CRM-ready notes and reports."""

from datetime import datetime


def format_crm_note(meeting_data: dict, compliance_report: dict) -> str:
    """Generate a CRM-ready plain text note.

    Args:
        meeting_data: Structured extraction from extract.py
        compliance_report: Compliance check results from compliance.py

    Returns:
        Formatted plain text note ready for CRM paste
    """
    lines = []

    # Header
    client = meeting_data.get("client_name", "Unknown Client")
    advisor = meeting_data.get("advisor_name", "Unknown Advisor")
    date = meeting_data.get("meeting_date") or datetime.now().strftime("%Y-%m-%d")
    meeting_type = _format_meeting_type(meeting_data.get("meeting_type", "general_checkup"))

    lines.append(f"CLIENT MEETING NOTE")
    lines.append(f"{'=' * 50}")
    lines.append(f"Client: {client}")
    lines.append(f"Advisor: {advisor}")
    lines.append(f"Date: {date}")
    lines.append(f"Type: {meeting_type}")
    lines.append(f"Compliance Status: {compliance_report['overall_status']}")
    lines.append("")

    # Discussion Summary
    topics = meeting_data.get("discussion_topics", [])
    if topics:
        lines.append("DISCUSSION SUMMARY")
        lines.append("-" * 30)
        for topic in topics:
            lines.append(f"  - {topic}")
        lines.append("")

    # Client Goals
    goals = meeting_data.get("client_goals", [])
    if goals:
        lines.append("CLIENT GOALS & OBJECTIVES")
        lines.append("-" * 30)
        for goal in goals:
            lines.append(f"  - {goal}")
        lines.append("")

    # Portfolio Discussion
    allocation = meeting_data.get("current_allocation")
    changes = meeting_data.get("proposed_changes")
    if allocation or changes:
        lines.append("PORTFOLIO")
        lines.append("-" * 30)
        if allocation:
            lines.append(f"  Current: {allocation}")
        if changes:
            lines.append(f"  Proposed: {changes}")
        lines.append("")

    # Products Discussed
    products = meeting_data.get("products_discussed", [])
    if products:
        lines.append("PRODUCTS DISCUSSED")
        lines.append("-" * 30)
        for p in products:
            action_label = p.get("action", "discussed").upper()
            lines.append(f"  [{action_label}] {p.get('product', 'N/A')}")
            if p.get("details"):
                lines.append(f"           {p['details']}")
        lines.append("")

    # Action Items
    actions = meeting_data.get("action_items", [])
    if actions:
        lines.append("ACTION ITEMS")
        lines.append("-" * 30)
        for i, a in enumerate(actions, 1):
            owner = a.get("owner", "advisor").upper()
            deadline = f" (by {a['deadline']})" if a.get("deadline") else ""
            lines.append(f"  {i}. [{owner}] {a.get('task', 'N/A')}{deadline}")
        lines.append("")

    # Compliance Summary
    lines.append("COMPLIANCE CHECK")
    lines.append("-" * 30)
    for rule_key, rule_result in compliance_report.get("rules", {}).items():
        status_icon = {"GREEN": "[PASS]", "YELLOW": "[REVIEW]", "RED": "[FLAG]"}
        icon = status_icon.get(rule_result["status"], "[?]")
        lines.append(f"  {icon} {rule_result['rule']}")
        for flag in rule_result.get("flags", []):
            lines.append(f"         {flag}")
    lines.append("")

    # Key Quotes
    quotes = meeting_data.get("key_quotes", [])
    if quotes:
        lines.append("KEY CLIENT QUOTES")
        lines.append("-" * 30)
        for q in quotes:
            lines.append(f'  "{q}"')
        lines.append("")

    # Next Steps
    next_meeting = meeting_data.get("next_meeting")
    if next_meeting:
        lines.append(f"NEXT MEETING: {next_meeting}")
        lines.append("")

    lines.append(f"{'=' * 50}")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("AI-assisted documentation â review before filing")

    return "\n".join(lines)


def format_compliance_panel(compliance_report: dict) -> dict:
    """Format compliance report for frontend display.

    Returns a structured dict optimized for the React compliance panel.
    """
    rules_display = []
    for key, result in compliance_report.get("rules", {}).items():
        rules_display.append({
            "id": key,
            "name": result["rule"],
            "status": result["status"],
            "color": {"GREEN": "#4CAF50", "YELLOW": "#FF9800", "RED": "#f44336"}[result["status"]],
            "flags": result.get("flags", []),
            "recommendation": result.get("recommendation", "")
        })

    return {
        "overall": compliance_report["overall_status"],
        "overall_color": {
            "GREEN": "#4CAF50",
            "YELLOW": "#FF9800",
            "RED": "#f44336"
        }[compliance_report["overall_status"]],
        "rules": rules_display,
        "action_count": len(compliance_report.get("action_required", []))
    }


def _format_meeting_type(meeting_type: str) -> str:
    return {
        "initial_consultation": "Initial Consultation",
        "quarterly_review": "Quarterly Review",
        "portfolio_rebalance": "Portfolio Rebalance",
        "retirement_planning": "Retirement Planning",
        "estate_planning": "Estate Planning",
        "tax_planning": "Tax Planning",
        "general_checkup": "General Check-up",
        "other": "Other"
    }.get(meeting_type, meeting_type.replace("_", " ").title())
