from dataclasses import dataclass
from typing import Callable, Optional
import json
import os

try:
    import anthropic
except ImportError:
    anthropic = None


@dataclass
class OpportunityRow:
    name: str
    deadline: str
    eligibility: str
    url: str


PLANNING_PROMPT = """
You are the planning brain of OpportunityScout.

User request:
{user_query}

Return ONLY a JSON array containing 2 or 3 short web search queries.
"""


EXTRACTION_PROMPT = """
You are the verification brain of OpportunityScout.

User request:
{user_query}

Live webpage text:
{page_text}

Return ONLY JSON:
{{
  "match": true,
  "name": "...",
  "deadline": "...",
  "eligibility": "..."
}}

If it does not match, return:
{{"match": false}}
"""


def call_claude(prompt: str) -> str:
    if anthropic is None:
        raise RuntimeError("The 'anthropic' package is not installed.")

    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set.")

    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.content[0].text


def clean_json(text):
    text = text.strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    return json.loads(text)


def run_agent(
    user_query: str,
    webcmd_search: Callable[[str], list],
    webcmd_open: Callable[[str], str],
    on_status: Optional[Callable[[str], None]] = None,
    max_pages_to_open: int = 6,
    demo_mode: bool = False
):

    def status(message):
        if on_status:
            on_status(message)

    status("Understanding request")

    if demo_mode:
        queries = [
            "AI ML hackathons India students 2026",
            "AI hackathon India college students",
            "ML hackathon India registration 2026"
        ]
    else:
        status("Planning search strategy")

        planning = call_claude(
            PLANNING_PROMPT.format(
                user_query=user_query
            )
        )

        queries = clean_json(planning)

    candidates = []

    for query in queries[:3]:

        status("Searching live web sources")

        found = webcmd_search(query)

        if found:
            candidates.extend(found)

    unique = []
    seen = set()

    for candidate in candidates:

        key = candidate.get("title", "")

        if key in seen:
            continue

        seen.add(key)
        unique.append(candidate)

    results = []

    for candidate in unique[:max_pages_to_open]:

        status("Verifying live opportunity")

        url = candidate.get("url", "")

        if demo_mode:

            results.append(
                OpportunityRow(
                    name=candidate.get("title", "Opportunity"),
                    deadline="See opportunity page",
                    eligibility="College students",
                    url=url
                )
            )

            continue

        if not url:
            continue

        status("Opening opportunity page")

        try:
            page_text = webcmd_open(url)
        except Exception:
            continue

        if not page_text:
            continue

        status("Checking eligibility")

        status("Extracting deadline")

        try:
            extraction = call_claude(
                EXTRACTION_PROMPT.format(
                    user_query=user_query,
                    page_text=page_text[:12000]
                )
            )

            data = clean_json(extraction)

        except Exception:
            continue

        if not data.get("match"):
            continue

        results.append(
            OpportunityRow(
                name=data.get(
                    "name",
                    candidate.get("title", "")
                ),
                deadline=data.get("deadline", ""),
                eligibility=data.get("eligibility", ""),
                url=url
            )
        )

    if not results:
        status("No verified matches found")
        return []

    status("Done")

    return results