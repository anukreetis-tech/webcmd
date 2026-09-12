import json
import subprocess


SESSION = "opportunity-scout-8y"


class WebcmdError(Exception):
    pass


def run_webcmd(script):
    result = subprocess.run(
        [
            "webcmd.cmd",
            "--session",
            SESSION,
            "browser",
            "run",
            "--stdin"
        ],
        input=script,
        text=True,
        capture_output=True,
        shell=True
    )

    if result.returncode != 0:
        raise WebcmdError(result.stderr or "Webcmd failed")

    try:
        output = json.loads(result.stdout)
        return output.get("result")
    except Exception:
        raise WebcmdError(
            "Could not parse Webcmd response: " + result.stdout
        )


def webcmd_search(query):
    """
    Search live Devfolio hackathons using Webcmd.
    """

    script = f"""
const query = {json.dumps(query)};

await page.goto(
    'https://devfolio.co/hackathons',
    {{
        waitUntil: 'domcontentloaded',
        timeout: 30000
    }}
);

await page.waitForTimeout(3000);

const items = await page.locator('a').evaluateAll(els =>
    els.map(a => ({{
        title: (a.innerText || '').trim(),
        url: a.href,
        text: a.parentElement
            ? a.parentElement.innerText
            : ''
    }}))
    .filter(x =>
        x.url &&
        x.url.includes('/hackathons/') &&
        x.title
    )
);

const terms = query
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter(x => x.length > 2);

const scored = items.map(item => {{
    const text = (item.title + ' ' + item.text).toLowerCase();

    const score = terms.filter(term =>
        text.includes(term)
    ).length;

    return {{
        title: item.title,
        url: item.url,
        snippet: item.text.slice(0, 500),
        score
    }};
}});

const seen = new Set();

const results = scored
    .filter(item => {{
        if (seen.has(item.url)) return false;
        seen.add(item.url);
        return true;
    }})
    .sort((a, b) => b.score - a.score)
    .slice(0, 10);

return results;
"""

    return run_webcmd(script)


def webcmd_open(url):
    """
    Open an individual opportunity page using Webcmd.
    """

    script = f"""
await page.goto(
    {json.dumps(url)},
    {{
        waitUntil: 'domcontentloaded',
        timeout: 30000
    }}
);

await page.waitForTimeout(2000);

return await page.locator('body').innerText();
"""

    return run_webcmd(script)