# Advisor Meeting AI Notetaker

**Turn a financial advisor's client-meeting recording into a compliant, CRM-ready note in 30 seconds — with SEC/FINRA suitability checks built in.**

Most financial advisors spend 40% of their day on documentation. This tool cuts that to under 5 minutes.

## What It Does

1. **Transcribes** the meeting recording (Whisper)
2. **Extracts** structured data — client goals, risk signals, products discussed, action items
3. **Runs compliance checks** — FINRA 2111 (Suitability), Reg BI (Best Interest), FINRA 4512 (Customer Info), SEC 17a-4 (Recordkeeping)
4. **Generates a CRM-ready note** formatted for paste into Salesforce, Wealthbox, Redtail, or any CRM

## The Compliance Layer (The Hard Part)

Every extraction gets a traffic-light compliance panel:

- **GREEN** — All clear, ready to file
- **YELLOW** — Needs manual review (ambiguous language, missing info)
- **RED** — Potential violation flagged (unsuitable product recommendation, missing risk documentation)

This catches things like:
- Risk-averse client language paired with aggressive product recommendations
- Missing risk tolerance assessment for new clients
- Product recommendations without documented alternatives or cost disclosures

## Architecture

```
Audio File → Whisper → LLM Extraction → Rule Engine → Formatted Output
```

**Backend:** Python + FastAPI | **Frontend:** React + Vite
**Transcription:** OpenAI Whisper | **Extraction:** GPT-4o or Claude via OpenRouter
**Compliance:** Custom rule engine mapping SEC/FINRA requirements

## Quick Start

```bash
cd backend && pip install -r requirements.txt
export OPENROUTER_API_KEY=your_key
python main.py
```

## Compliance Rules Checked

| Rule | What It Checks |
|------|---------------|
| FINRA 2111 | Suitability: recommendations match client risk profile? |
| Reg BI | Best Interest: alternatives considered, costs disclosed? |
| FINRA 4512 | Customer Info: required information documented? |
| SEC 17a-4 | Recordkeeping: decisions and communications recorded? |

## Sample Meetings Included

1. **Retirement Review** — Suitability flag (risk-averse + aggressive allocation)
2. **Portfolio Rebalance** — All compliance checks green
3. **New Client Onboarding** — Red flag on missing risk documentation

## Why I Built This

I work with wealthtech startups building advisor tooling. The documentation bottleneck is the most consistent pain point — and most AI note-taking solutions skip the compliance layer entirely.

Compliance is the foundation. Build it into the extraction pipeline from day one.

**Full architecture breakdown:** [architmittal.com](https://architmittal.com)

## License

MIT

---

Built by [Archit Mittal](https://architmittal.com) — AI & Automation Consultant for Financial Services
