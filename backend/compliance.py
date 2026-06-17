"""SEC/FINRA compliance and suitability checks for advisor meeting notes."""

from typing import Optional


# Compliance rule definitions
COMPLIANCE_RULES = {
    "finra_2111_suitability": {
        "name": "FINRA Rule 2111 â Suitability",
        "description": "Recommendations must be suitable based on client's investment profile",
        "checks": [
            "risk_tolerance_documented",
            "recommendation_matches_profile",
            "no_unsuitable_products"
        ]
    },
    "reg_bi_best_interest": {
        "name": "Regulation Best Interest (Reg BI)",
        "description": "Broker-dealers must act in the best interest of retail customers",
        "checks": [
            "alternatives_considered",
            "costs_disclosed",
            "conflicts_disclosed"
        ]
    },
    "finra_4512_customer_info": {
        "name": "FINRA Rule 4512 â Customer Account Information",
        "description": "Required customer information must be collected and maintained",
        "checks": [
            "identity_verified",
            "financial_situation_documented",
            "investment_objectives_recorded"
        ]
    },
    "sec_17a4_recordkeeping": {
        "name": "SEC Rule 17a-4 â Recordkeeping",
        "description": "Records must be preserved in required format and duration",
        "checks": [
            "meeting_documented",
            "decisions_recorded",
            "communications_preserved"
        ]
    }
}


def run_compliance_check(meeting_data: dict) -> dict:
    """Run compliance checks against extracted meeting data.

    Args:
        meeting_data: Structured meeting data from extract.py

    Returns:
        Compliance report with traffic-light status per rule
    """
    results = {}

    results["finra_2111_suitability"] = _check_suitability(meeting_data)
    results["reg_bi_best_interest"] = _check_best_interest(meeting_data)
    results["finra_4512_customer_info"] = _check_customer_info(meeting_data)
    results["sec_17a4_recordkeeping"] = _check_recordkeeping(meeting_data)

    overall = _compute_overall(results)

    return {
        "overall_status": overall,
        "rules": results,
        "summary": _generate_summary(results),
        "action_required": [
            r for r in results.values()
            if r["status"] in ("RED", "YELLOW")
        ]
    }


def _check_suitability(data: dict) -> dict:
    """Check FINRA 2111 suitability requirements."""
    flags = []
    status = "GREEN"

    risk_signals = data.get("risk_signals", [])
    products = data.get("products_discussed", [])
    client_goals = data.get("client_goals", [])

    # Check for high-severity risk signals
    high_risk = [s for s in risk_signals if s.get("severity") == "high"]
    if high_risk:
        status = "RED"
        for signal in high_risk:
            flags.append(f"High-risk signal: {signal.get('signal', 'Unknown')}")

    # Check for medium-severity risk signals
    med_risk = [s for s in risk_signals if s.get("severity") == "medium"]
    if med_risk and status != "RED":
        status = "YELLOW"
        for signal in med_risk:
            flags.append(f"Review needed: {signal.get('signal', 'Unknown')}")

    # Check if recommendations align with stated goals
    recommended = [p for p in products if p.get("action") == "recommended"]
    if recommended and not client_goals:
        if status != "RED":
            status = "YELLOW"
        flags.append("Products recommended but no clear client goals documented")

    # Check for risk tolerance language vs product risk
    risk_averse_keywords = ["can't afford to lose", "conservative", "safe", "no risk",
                           "guaranteed", "preserve capital", "nervous", "worried about losses"]
    aggressive_products = ["growth fund", "equity", "stock", "crypto", "leveraged",
                          "options", "futures", "speculative", "emerging market"]

    transcript_lower = " ".join(
        s.get("signal", "") for s in risk_signals
    ).lower() + " ".join(
        g.lower() for g in client_goals
    )

    has_risk_averse = any(kw in transcript_lower for kw in risk_averse_keywords)
    has_aggressive = any(
        any(kw in p.get("product", "").lower() or kw in p.get("details", "").lower()
            for kw in aggressive_products)
        for p in recommended
    )

    if has_risk_averse and has_aggressive:
        status = "RED"
        flags.append("SUITABILITY CONCERN: Risk-averse language detected alongside aggressive product recommendations")

    if not flags:
        flags.append("No suitability concerns identified")

    return {
        "rule": COMPLIANCE_RULES["finra_2111_suitability"]["name"],
        "status": status,
        "flags": flags,
        "recommendation": _suitability_recommendation(status)
    }


def _check_best_interest(data: dict) -> dict:
    """Check Regulation Best Interest requirements."""
    flags = []
    status = "GREEN"

    products = data.get("products_discussed", [])
    recommended = [p for p in products if p.get("action") == "recommended"]

    if len(recommended) > 0:
        # Check if alternatives were mentioned
        has_alternatives = len(products) > len(recommended)
        if not has_alternatives:
            if status != "RED":
                status = "YELLOW"
            flags.append("Product recommended without documented alternatives considered")

        # Check if costs were discussed
        cost_keywords = ["fee", "cost", "expense ratio", "commission", "load", "charge"]
        has_cost_discussion = any(
            any(kw in p.get("details", "").lower() for kw in cost_keywords)
            for p in products
        )
        if not has_cost_discussion and recommended:
            if status != "RED":
                status = "YELLOW"
            flags.append("No cost/fee discussion documented for recommended products")

    if not flags:
        flags.append("Best interest requirements appear satisfied")

    return {
        "rule": COMPLIANCE_RULES["reg_bi_best_interest"]["name"],
        "status": status,
        "flags": flags,
        "recommendation": "Document cost comparisons and alternatives considered" if status != "GREEN" else "No action needed"
    }


def _check_customer_info(data: dict) -> dict:
    """Check FINRA 4512 customer information requirements."""
    flags = []
    status = "GREEN"

    meeting_type = data.get("meeting_type", "")
    client_goals = data.get("client_goals", [])
    risk_signals = data.get("risk_signals", [])

    if meeting_type == "initial_consultation":
        # New client â more documentation required
        if not client_goals:
            status = "RED"
            flags.append("MISSING: Investment objectives not documented for new client")
        if not risk_signals:
            status = "RED"
            flags.append("MISSING: Risk tolerance not assessed for new client")
        if data.get("client_name") == "Unknown Client":
            status = "RED"
            flags.append("MISSING: Client identity not documented")
    else:
        # Existing client â lighter requirements
        if not client_goals and not risk_signals:
            if status != "RED":
                status = "YELLOW"
            flags.append("Consider documenting current goals and risk profile updates")

    if not flags:
        flags.append("Customer information requirements satisfied")

    return {
        "rule": COMPLIANCE_RULES["finra_4512_customer_info"]["name"],
        "status": status,
        "flags": flags,
        "recommendation": "Complete customer information form" if status == "RED" else "No action needed"
    }


def _check_recordkeeping(data: dict) -> dict:
    """Check SEC 17a-4 recordkeeping requirements."""
    flags = []
    status = "GREEN"

    action_items = data.get("action_items", [])
    discussion_topics = data.get("discussion_topics", [])

    if not discussion_topics:
        status = "YELLOW"
        flags.append("Meeting topics not clearly documented")

    if not action_items:
        status = "YELLOW"
        flags.append("No action items documented â confirm none were discussed")

    # Check for proposed changes without documentation
    if data.get("proposed_changes") and not action_items:
        status = "YELLOW"
        flags.append("Portfolio changes discussed but no action items to track execution")

    if not flags:
        flags.append("Recordkeeping requirements satisfied")

    return {
        "rule": COMPLIANCE_RULES["sec_17a4_recordkeeping"]["name"],
        "status": status,
        "flags": flags,
        "recommendation": "Ensure all discussed changes are documented with action items" if status != "GREEN" else "No action needed"
    }


def _compute_overall(results: dict) -> str:
    statuses = [r["status"] for r in results.values()]
    if "RED" in statuses:
        return "RED"
    if "YELLOW" in statuses:
        return "YELLOW"
    return "GREEN"


def _suitability_recommendation(status: str) -> str:
    if status == "RED":
        return "IMMEDIATE REVIEW REQUIRED: Potential suitability violation detected. Escalate to compliance officer before proceeding."
    if status == "YELLOW":
        return "Manual review recommended before finalizing documentation."
    return "No suitability concerns. Documentation ready for CRM."


def _generate_summary(results: dict) -> str:
    lines = []
    for key, result in results.items():
        icon = {"GREEN": "PASS", "YELLOW": "REVIEW", "RED": "FLAG"}[result["status"]]
        lines.append(f"[{icon}] {result['rule']}")
        for flag in result["flags"]:
            lines.append(f"    - {flag}")
    return "\n".join(lines)
