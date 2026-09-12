const userQuery = "AI ML hackathons in India";
await page.goto('https://devfolio.co/hackathons', { waitUntil: 'domcontentloaded', timeout: 30000 });
await page.waitForTimeout(3000);
const links = await page.locator('a').evaluateAll(els => els.map(a => ({
  name: (a.innerText || '').trim(),
  link: a.getAttribute('href') || '',
  context: a.parentElement ? a.parentElement.innerText : ''
})).filter(item => {
  return item.link &&
    item.link.includes('/hackathons/') &&
    !item.link.endsWith('/hackathons/');
}));
const unique = [];
const seen = new Set();
for (const item of links) {
  if (!item.name || item.name.length < 3) continue;
  if (seen.has(item.link)) continue;
  seen.add(item.link);
  unique.push(item);
}
const stopWords = ['find', 'show', 'me', 'the', 'a', 'an', 'in', 'on', 'for', 'this', 'month', 'that', 'are', 'is', 'and', 'opportunities', 'opportunity'];
const terms = userQuery.toLowerCase().split(/[^a-z0-9]+/).filter(x => x.length > 2 && !stopWords.includes(x));
const scored = unique.map(item => {
  const text = (item.name + ' ' + item.context).toLowerCase();
  const matches = terms.filter(term => text.includes(term));
  return { ...item, score: matches.length };
});
let selected = scored.filter(item => item.score > 0);
if (selected.length === 0) {
  selected = scored.slice(0, 12);
}
selected = selected.slice(0, 12);
return selected.map(item => ({
  name: item.name,
  type: 'Hackathon',
  source: 'Devfolio',
  link: item.link.startsWith('http')
    ? item.link
    : 'https://devfolio.co' + item.link
}));