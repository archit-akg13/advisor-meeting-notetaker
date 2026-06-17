"""LLM-powered structured extraction from meeting transcripts."""

import json
import os
from typing import Optional

EXTRACTION_PROMPT = """You are an expert financial services documentation assistant.
Analyze this advisor-client meeting transcript and extract structured information.

TRANSCRIPT:
{transcript}

Extract the following as JSON (use null for any field you cannot determine):

{{
  "client_name": "Name of the client (or 'Unknown Client' if not mentioned)",
  "advisor_name": "Name of the advisor (or 'Unknown Advisor' if not mentioned)",
  "meeting_date": "Date mentioned or null",
  "meeting_type": "One of: initial_consultation, quarterly_review, portfolio_rebalance, retirement_planning, estate_planning, tax_planning, general_checkup, other",
  "discussion_topics": ["List of main topics discussed"],
  "client_goals": ["Specific goals or objectives the client expressed"],
  "risk_signals": [
    {{
      "signal": "What was said",
      "severity": "low|medium|high",
      "context": "Surrounding context"
    }}
  ],
  "products_discussed": [
    {{
      "product": "Name or type of product/fund/instrument",
      "action": "recommended|discussed|existing|removed",
      "details": "Any specifics mentioned"
    }}
  ],
  "action_items": [
    {{
      "task": "What needs to be done",
      "owner": "advisor|client|both",
      "deadline": "If mentioned, otherwise null"
    }}
  ],
  "key_quotes": ["Important direct quotes from the client (max 5)"],
  "current_allocation": "If discussed, brief description of current portfolio",
  "proposed_changes": "If discussed, brief description of proposed changes",
  "next_meeting": "If scheduled, when"
}}

Be precise. Only include information explicitly stated or strongly implied in the transcript.
Do not fabricate details. If something is ambiguous, note it in the relevant field."""


async def extract_meeting_data(transcript: str, provider: str = "openrouter") -> dict:
    """Extract structured data from meeting transcript using LLM.

    Args:
        transcript: Full meeting transcript text
        provider: 'openrouter' (default), 'openai', or 'anthropic'

    Returns:
        Structured meeting data as dict
    """
    prompt = EXTRACTION_PROMPT.format(transcript=transcript)

    if provider == "anthropic":
        return await _extract_with_anthropic(prompt)
    if provider == "openrouter":
        return await _extract_with_openrouter(prompt)
    return await _extract_with_openai(prompt)


async def _extract_with_openrouter(prompt: str) -> dict:
    """Use OpenRouter API (OpenAI-compatible, routes to any model)."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1"
    )
    model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4")

    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt + "\n\nRespond with ONLY valid JSON, no markdown fences."}],
        temperature=0.1,
    )
    text = response.choices[0].message.content.strip()
    # Strip markdown fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(text)


async def _extract_with_openai(prompt: str) -> dict:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)


async def _extract_with_anthropic(prompt: str) -> dict:
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt + "\n\nRespond with ONLY the JSON object, no markdown."}],
        temperature=0.1
    )
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(text)
