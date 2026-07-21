import json
from typing import Any

# pyrefly: ignore [missing-import]
import google.generativeai as genai

from app.config import get_settings


async def generate_ai_summary(url: str, scan_results: dict[str, Any]) -> str:
    """
    Use Google Gemini 2.5 Flash to generate a plain-language summary
    of scan results with actionable fix suggestions.

    Returns a JSON string containing per-check explanations and an overall summary.
    """
    settings = get_settings()

    if not settings.GEMINI_API_KEY:
        return json.dumps({
            "overall_summary": "AI analysis is not available — no API key configured.",
            "explanations": [],
        })

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = f"""You are a website security expert explaining scan results to a non-technical website owner.

I scanned the website: {url}
Here are the raw scan results in JSON:

{json.dumps(scan_results, indent=2)}

Please analyze these results and return a JSON response with this exact structure:
{{
  "overall_summary": "A 2-3 sentence overall assessment of the website's security posture. Be specific about the most critical issues.",
  "explanations": [
    {{
      "check_name": "The name of the security check",
      "status": "warning" or "failed",
      "explanation": "A simple, non-technical explanation of what this check means and why it matters.",
      "fix_suggestion": "A concrete, actionable step the website owner can take to fix this issue."
    }}
  ]
}}

Rules:
- Include entries in "explanations" ONLY for security checks that did NOT pass or have 'warning' or 'critical' status/severity (i.e. where severity is not "ok" or passed is false).
- Do NOT include any entries in "explanations" for checks that passed successfully or are 'ok'.
- Use simple language a non-technical person can understand.
- Be specific about the actual findings — do not be generic.
- For fix suggestions, mention specific tools, services, or configuration changes when relevant.
- Return ONLY valid JSON, no markdown formatting or code fences."""

    try:
        response = await model.generate_content_async(prompt)
        response_text = response.text.strip()

        # Clean up potential markdown code fences from the response
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        # Validate the JSON structure
        parsed = json.loads(response_text)
        if "overall_summary" not in parsed or "explanations" not in parsed:
            raise ValueError("Response missing required fields")

        return response_text

    except json.JSONDecodeError:
        return json.dumps({
            "overall_summary": f"Security scan completed for {url}. Score: {scan_results.get('score', 'N/A')}/100. "
                               f"{scan_results.get('summary', {}).get('passed', 0)} checks passed, "
                               f"{scan_results.get('summary', {}).get('failed', 0)} checks failed.",
            "explanations": [],
        })
    except Exception as exc:
        return json.dumps({
            "overall_summary": f"AI analysis encountered an error: {str(exc)}. "
                               f"Scan score: {scan_results.get('score', 'N/A')}/100.",
            "explanations": [],
        })
