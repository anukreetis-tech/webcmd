from bridge import run_webcmd

code = """
await page.goto("https://devfolio.co/hackathons/open");
await page.waitForTimeout(3000);
return await page.locator("body").innerText();
"""

result = run_webcmd(code)

print(result.get("result", "")[:5000])