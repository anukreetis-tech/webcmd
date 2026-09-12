import subprocess
import json
import tempfile
import os


SESSION = "opportunity-scout-8y"


def run_webcmd(code):
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".js",
            delete=False,
            encoding="utf-8"
        ) as f:
            f.write(code)
            temp_path = f.name

        result = subprocess.run(
            [
                "webcmd.cmd",
                "--session",
                SESSION,
                "browser",
                "run",
                "--file",
                temp_path,
                "--timeout",
                "60"
            ],
            capture_output=True,
            text=True,
            shell=True
        )

        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout)

        return json.loads(result.stdout)

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

def webcmd_search(query):
    code = """
await page.goto("https://devfolio.co/hackathons/open", {
    waitUntil: "domcontentloaded",
    timeout: 30000
});

await page.waitForTimeout(3000);

const text = await page.locator("body").innerText();

return text;
"""

    data = run_webcmd(code)
    text = data.get("result", "")

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    opportunities = []

    for i, line in enumerate(lines):
        if line == "Hackathon" and i > 0:
            name = lines[i - 1]

            if name not in opportunities:
                opportunities.append(name)

    return [
        {
            "title": name,
            "url": "",
            "snippet": ""
        }
        for name in opportunities[:15]
    ]


def webcmd_open(url):
    safe_url = json.dumps(url)

    code = f"""
await page.goto({safe_url}, {{
    waitUntil: "domcontentloaded",
    timeout: 30000
}});

await page.waitForTimeout(1500);

return await page.locator("body").innerText();
"""

    data = run_webcmd(code)

    return data.get("result", "")