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
You are the planning brain of a browser agent called OpportunityScout.

User request:
{user_query}

Create 2 or 3 short web search queries that will help find CURRENT and OPEN
opportunities matching the request.

Focus on:
- current opportunities
- application or registration deadlines
- college/student eligibility
- India when requested
- AI/ML when requested

Return ONLY a JSON array of search query strings.
Example:
["AI ML hackathons India students 2026",
 "AI hackathon India college students",
 "ML hackathon India registration 2026"]
"""


EXTRACTION_PROMPT = """
You are the verification and extraction brain of OpportunityScout.

Original user request:
{user_query}

Here is text extracted from a live webpage:
---
{page_text}
---

Determine whether this webpage describes a real opportunity matching the
user's request.

Only accept an opportunity if the information is supported by the webpage.
Do NOT guess missing information.

Return ONLY valid JSON in this format:

{{
  "match": true,
  "name": "...",
  "deadline": "...",
  "eligibility": "..."
}}

If it does not match, return:

{{
  "match": false
}}
"""


SUMMARY_NOTE_PROMPT = """
You are the final verification brain of OpportunityScout.

User request:
{user_query}

Candidate opportunities:
{candidates}

Remove duplicates and keep only useful matching opportunities.

Return ONLY a JSON array containing objects with:
name
deadline
eligibility
url
"""


def call_claude(prompt: str) -> str:
    if anthropic is None:
        raise RuntimeError(
            "The 'anthropic' package is not installed."
        )

    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set."
        )

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


def clean_json(text: str):
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
) -> list[OpportunityRow]:

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
        planning = call_claude(
            PLANNING_PROMPT.format(
                user_query=user_query
            )
        )

        queries = clean_json(planning)

    status("Planning search strategy")

    candidates = []

    for query in queries[:3]:
        status("Searching live web sources")

        found = webcmd_search(query)

        if found:
            candidates.extend(found)

    unique = []
    seen = set()

    for candidate in candidates:
        url = candidate.get("url", "")

        if not url:
            continue

        if url in seen:
            continue

        seen.add(url)
        unique.append(candidate)

    results = []

    for candidate in unique[:max_pages_to_open]:

        status("Opening opportunity page")

        url = candidate.get("url", "")

        try:
            page_text = webcmd_open(url)
        except Exception:
            continue

        if not page_text:
            continue

        status("Checking eligibility")

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
                name=data.get("name", candidate.get("title", "")),
                deadline=data.get("deadline", ""),
                eligibility=data.get("eligibility", ""),
                url=url
            )
        )

    if not results:
        status("No verified matches found")
        return []

    if len(results) > 1 and not demo_mode:

        status("Verifying and removing duplicates")

        candidate_data = [
            {
                "name": item.name,
                "deadline": item.deadline,
                "eligibility": item.eligibility,
                "url": item.url
            }
            for item in results
        ]

        try:
            summary = call_claude(
                SUMMARY_NOTE_PROMPT.format(
                    user_query=user_query,
                    candidates=json.dumps(candidate_data)
                )
            )

            final_data = clean_json(summary)

            results = [
                OpportunityRow(
                    name=item.get("name", ""),
                    deadline=item.get("deadline", ""),
                    eligibility=item.get("eligibility", ""),
                    url=item.get("url", "")
                )
                for item in final_data
            ]

        except Exception:
            pass

    status("Done")

    return results


if __name__ == "__main__":
    print("OpportunityScout Agent Brain")