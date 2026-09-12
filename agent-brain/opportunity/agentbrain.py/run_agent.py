import sys
import json

from agentbrain import run_agent
from bridge import webcmd_search, webcmd_open, WebcmdError


def status(message):
    print(
        json.dumps({"status": message}),
        file=sys.stderr
    )


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "AI ML hackathons in India"

    try:
        rows = run_agent(
            query,
            webcmd_search=webcmd_search,
            webcmd_open=webcmd_open,
            on_status=status,
            max_pages_to_open=6,
            demo_mode=False
        )

        result = []

        for row in rows:
            result.append({
                "name": row.name,
                "deadline": row.deadline,
                "eligibility": row.eligibility,
                "url": row.url
            })

        print(json.dumps({
            "success": True,
            "query": query,
            "opportunities": result
        }))

    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": str(e)
        }))
        sys.exit(1)