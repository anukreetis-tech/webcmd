import sys
import json
import importlib.util

spec = importlib.util.spec_from_file_location(
    "agentbrain",
    r"agentbrain_new.py"
)

agentbrain = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agentbrain)

run_agent = agentbrain.run_agent

from bridge import webcmd_search, webcmd_open


def status(message):
    print(message, file=sys.stderr, flush=True)


query = (
    sys.argv[1]
    if len(sys.argv) > 1
    else "AI ML hackathons in India for college students"
)


try:
    results = run_agent(
        user_query=query,
        webcmd_search=webcmd_search,
        webcmd_open=webcmd_open,
        on_status=status,
        max_pages_to_open=6,
        demo_mode=True
    )

    output = []

    for item in results:
        output.append({
            "name": item.name,
            "deadline": item.deadline,
            "eligibility": item.eligibility,
            "url": item.url
        })

    print(json.dumps(output))

except Exception as e:
    print(json.dumps({
        "error": str(e)
    }))
    sys.exit(1)