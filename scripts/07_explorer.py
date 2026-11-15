"""
Step 4 - A small explorer to browse the posts: outputs/explorer.html

One self-contained HTML file (data inside, plain JavaScript, no library, no build step).
Open it in any browser. Per brand: top emojis, like rate per category, and the posts
themselves, filtered by topic, emoji type and tone.

Run from the ma1/ folder:  .venv/bin/python scripts/07_explorer.py
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / "data" / "04_topic.csv", dtype={"id": str}, keep_default_na=False)

posts = [{
    "id": r.id, "brand": r.brand, "type": r.post_type, "date": r.created_at[:10], "text": r.text,
    "topic": r.topic, "tone": r.vader_label, "usage": r.emoji_usage,
    "face": int(r.has_face), "nonface": int(r.has_nonface),
    "emojis": r.emojis.split(" ") if r.emojis else [],
    "like": int(r.like), "view": int(r.view), "rate": round(100 * r.like / r.view, 2),
} for r in df.itertuples()]

# "</" inside a post must not close the <script> tag
data = json.dumps(posts, ensure_ascii=False).replace("</", "<\\/")

HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Brewhaus vs Trailnorth: post explorer</title>
<style>
  :root {
    --surface: #fcfcfb; --card: #ffffff; --text: #0b0b0b; --text2: #52514e; --muted: #898781;
    --line: #e1e0d9; --brewhaus: #eb6834; --trailnorth: #2a78d6;
  }
  @media (prefers-color-scheme: dark) {
    :root { --surface: #1a1a19; --card: #222220; --text: #f0efec; --text2: #c3c2b7; --muted: #898781;
            --line: #2c2c2a; --brewhaus: #d95926; --trailnorth: #3987e5; }
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--surface); color: var(--text);
         font: 15px/1.45 -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; }
  main { max-width: 1120px; margin: 0 auto; padding: 28px 16px 60px; }
  h1 { font-size: 22px; margin: 0 0 4px; }
  h2 { font-size: 15px; margin: 0 0 12px; }
  p.lead { color: var(--text2); margin: 0 0 20px; max-width: 70ch; }
  .card { background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 16px; }
  .filters { display: flex; flex-wrap: wrap; gap: 12px 18px; align-items: end; margin-bottom: 16px; }
  .filters label { display: block; font-size: 12px; color: var(--muted); margin-bottom: 4px; }
  select, button { font: inherit; color: var(--text); background: var(--card); border: 1px solid var(--line);
                   border-radius: 7px; padding: 6px 10px; cursor: pointer; }
  select:focus-visible, button:focus-visible { outline: 2px solid var(--trailnorth); outline-offset: 2px; }
  .seg { display: inline-flex; }
  .seg button { border-radius: 0; margin-left: -1px; }
  .seg button:first-child { border-radius: 7px 0 0 7px; margin-left: 0; }
  .seg button:last-child { border-radius: 0 7px 7px 0; }
  .seg button[aria-pressed="true"] { background: var(--text); color: var(--surface); border-color: var(--text); }
  .tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; margin-bottom: 12px; }
  .tile h2 { display: flex; align-items: center; gap: 8px; }
  .dot { width: 10px; height: 10px; border-radius: 50%; flex: none; display: inline-block; }
  .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(84px, 1fr)); gap: 8px 18px; }
  .card, .cols > div { min-width: 0; }
  td { overflow-wrap: anywhere; }
  .stats b { display: block; font-size: 20px; font-weight: 600; }
  .stats span { font-size: 12px; color: var(--muted); }
  .two { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.9fr); gap: 12px; margin-bottom: 12px; }
  @media (max-width: 820px) { .two { grid-template-columns: 1fr; } }
  .cols { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 18px; }
  .row { display: grid; grid-template-columns: 26px 1fr 30px; gap: 8px; align-items: center; margin: 5px 0; }
  .row .glyph { font-size: 18px; text-align: center; }
  .track { height: 12px; }
  .bar { height: 12px; border-radius: 0 4px 4px 0; min-width: 2px; }
  .num { font-size: 12.5px; color: var(--text2); font-variant-numeric: tabular-nums; }
  .sub { font-size: 12px; color: var(--muted); margin: 0 0 6px; }
  .cat { margin: 0 0 10px; }
  .cat .name { font-size: 13px; margin-bottom: 3px; }
  .cat .line { display: grid; grid-template-columns: minmax(50px, 1fr) 112px; gap: 8px; align-items: center; margin: 3px 0; }
  .cat .num { font-size: 12px; }
  .few { opacity: .4; }
  .note { font-size: 12px; color: var(--muted); margin: 10px 0 0; }
  .legend { display: flex; gap: 16px; font-size: 12.5px; color: var(--text2); margin-bottom: 10px; }
  .legend span { display: inline-flex; align-items: center; gap: 6px; }
  table { width: 100%; border-collapse: collapse; }
  th { text-align: left; font-size: 12px; font-weight: 500; color: var(--muted); padding: 6px 8px;
       border-bottom: 1px solid var(--line); white-space: nowrap; }
  td { padding: 9px 8px; border-bottom: 1px solid var(--line); vertical-align: top; }
  td.n { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
  td.id { white-space: nowrap; font-size: 12.5px; color: var(--text2); }
  .tag { display: inline-block; font-size: 11.5px; color: var(--text2); border: 1px solid var(--line);
         border-radius: 20px; padding: 0 7px; margin: 3px 4px 0 0; white-space: nowrap; }
  .bartop { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 8px; flex-wrap: wrap; }
  .empty { color: var(--muted); padding: 18px 0; }
  .scroll { overflow-x: auto; }
</style>
</head>
<body>
<main>
  <h1>Brewhaus vs Trailnorth: post explorer</h1>
  <p class="lead">The 348 posts we analysed (original posts and replies, 1 April to 30 September 2026).
  Pick a brand and filters; every number and the list of posts follow. Like rate = likes divided by views.</p>

  <div class="filters">
    <div><label id="lb">Brand</label>
      <div class="seg" role="group" aria-labelledby="lb" id="brand">
        <button data-v="both" aria-pressed="true">Both</button><button data-v="Brewhaus" aria-pressed="false">Brewhaus</button><button data-v="Trailnorth" aria-pressed="false">Trailnorth</button>
      </div></div>
    <div><label for="type">Posts</label>
      <select id="type"><option value="original">Original posts</option><option value="reply">Replies</option><option value="all">Originals and replies</option></select></div>
    <div><label for="topic">Topic</label>
      <select id="topic"><option value="all">All topics</option><option>Informational</option><option>Emotional</option><option>Mixed</option></select></div>
    <div><label for="emoji">Emoji</label>
      <select id="emoji"><option value="all">Any</option><option value="face">Has a face emoji</option><option value="nonface">Has a non-face emoji</option>
        <option value="with text">Emoji with the text</option><option value="instead of words">Emoji instead of a word</option>
        <option value="alone">Emoji alone (no words)</option><option value="none">No emoji</option></select></div>
    <div><label for="tone">Tone (VADER, emojis included)</label>
      <select id="tone"><option value="all">Any tone</option><option>positive</option><option>neutral</option><option>negative</option></select></div>
    <div><button id="reset">Reset</button></div>
  </div>

  <div class="tiles" id="tiles"></div>

  <div class="two">
    <section class="card"><h2>Most used emojis</h2><div class="cols" id="emojis"></div></section>
    <section class="card"><h2>Median like rate by category</h2>
      <div class="legend" id="legend"></div>
      <div class="cols" id="charts"></div>
      <p class="note">Bars compare the posts currently selected. A faded bar rests on fewer than 5 posts.
      These are descriptions, not the regression: other differences between posts are not held equal.</p>
    </section>
  </div>

  <section class="card">
    <div class="bartop"><h2 id="count" style="margin:0"></h2>
      <div><label for="sort" class="sub" style="display:inline">Sort </label>
        <select id="sort"><option value="high">Highest like rate</option><option value="low">Lowest like rate</option><option value="new">Newest</option></select></div></div>
    <div class="scroll"><table><thead><tr><th>Post</th><th>Text</th><th>Like rate</th><th>Likes</th><th>Views</th></tr></thead><tbody id="rows"></tbody></table></div>
    <p style="margin:12px 0 0"><button id="more">Show 25 more</button></p>
  </section>
</main>

<script>
const POSTS = /*DATA*/;
const BRANDS = ["Brewhaus", "Trailnorth"];
const COLOR = { Brewhaus: "var(--brewhaus)", Trailnorth: "var(--trailnorth)" };
const DIMS = [
  { title: "Topic", key: "topic", cats: [["Informational", "Informational"], ["Emotional", "Emotional"], ["Mixed", "Mixed"]] },
  { title: "Emoji use", key: "usage", cats: [["none", "No emoji"], ["with text", "With the text"], ["instead of words", "Instead of a word"], ["alone", "Alone"]] },
  { title: "Tone", key: "tone", cats: [["positive", "Positive"], ["neutral", "Neutral"], ["negative", "Negative"]] },
];
const state = { brand: "both", type: "original", topic: "all", emoji: "all", tone: "all", sort: "high", shown: 25 };
const $ = id => document.getElementById(id);
const esc = s => s.replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const median = a => { if (!a.length) return null; const s = [...a].sort((x, y) => x - y), m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };
const pct = v => v === null ? "n/a" : v.toFixed(2) + "%";

function selected() {
  return POSTS.filter(p =>
    (state.brand === "both" || p.brand === state.brand) &&
    (state.type === "all" || p.type === state.type) &&
    (state.topic === "all" || p.topic === state.topic) &&
    (state.tone === "all" || p.tone === state.tone) &&
    (state.emoji === "all" || (state.emoji === "face" ? p.face : state.emoji === "nonface" ? p.nonface : p.usage === state.emoji)));
}

function render() {
  const posts = selected();
  const brands = state.brand === "both" ? BRANDS : [state.brand];
  const of = b => posts.filter(p => p.brand === b);

  $("tiles").innerHTML = brands.map(b => {
    const ps = of(b), n = ps.length;
    const withEmoji = n ? Math.round(100 * ps.filter(p => p.emojis.length).length / n) + "%" : "n/a";
    const perPost = n ? (ps.reduce((s, p) => s + p.emojis.length, 0) / n).toFixed(1) : "n/a";
    return `<section class="card tile"><h2><span class="dot" style="background:${COLOR[b]}"></span>${b}</h2>
      <div class="stats"><div><b>${n}</b><span>posts</span></div><div><b>${pct(median(ps.map(p => p.rate)))}</b><span>median like rate</span></div>
      <div><b>${withEmoji}</b><span>with an emoji</span></div><div><b>${perPost}</b><span>emojis per post</span></div></div></section>`;
  }).join("");

  $("emojis").innerHTML = brands.map(b => {
    const counts = {};
    of(b).forEach(p => p.emojis.forEach(e => counts[e] = (counts[e] || 0) + 1));
    const top = Object.entries(counts).sort((x, y) => y[1] - x[1]).slice(0, 10), max = top.length ? top[0][1] : 1;
    const rows = top.map(([e, n]) => `<div class="row" title="${b}: ${e} used ${n} times"><span class="glyph">${e}</span>
      <div class="track"><div class="bar" style="width:${100 * n / max}%;background:${COLOR[b]}"></div></div><span class="num">${n}</span></div>`).join("");
    return `<div><p class="sub">${b} · ${Object.keys(counts).length} different emojis</p>${rows || '<p class="empty">No emoji in this selection.</p>'}</div>`;
  }).join("");

  $("legend").innerHTML = brands.map(b => `<span><span class="dot" style="background:${COLOR[b]}"></span>${b}</span>`).join("");
  $("charts").innerHTML = DIMS.map(d => {
    const cells = d.cats.map(([v, label]) => brands.map(b => { const ps = of(b).filter(p => p[d.key] === v); return { b, label, n: ps.length, m: median(ps.map(p => p.rate)) }; }));
    const max = Math.max(0.01, ...cells.flat().map(c => c.m || 0));
    return `<div><p class="sub">${d.title}</p>` + cells.map(group => `<div class="cat"><div class="name">${group[0].label}</div>` +
      group.map(c => c.n ? `<div class="line ${c.n < 5 ? "few" : ""}" title="${c.b}, ${c.label}: median like rate ${pct(c.m)} over ${c.n} posts">
          <div class="track"><div class="bar" style="width:${100 * c.m / max}%;background:${COLOR[c.b]}"></div></div>
          <span class="num">${pct(c.m)} · ${c.n} post${c.n > 1 ? "s" : ""}</span></div>`
        : `<div class="line few"><div class="track"></div><span class="num">no posts</span></div>`).join("") + `</div>`).join("") + `</div>`;
  }).join("");

  const order = { high: (a, b) => b.rate - a.rate, low: (a, b) => a.rate - b.rate, new: (a, b) => b.date.localeCompare(a.date) }[state.sort];
  const sorted = [...posts].sort(order);
  $("count").textContent = posts.length + (posts.length === 1 ? " post" : " posts");
  $("rows").innerHTML = sorted.slice(0, state.shown).map(p => `<tr>
    <td class="id"><span class="dot" style="background:${COLOR[p.brand]}"></span> ${p.id}<br>${p.date}</td>
    <td>${esc(p.text)}<br><span class="tag">${p.topic}</span><span class="tag">${p.tone}</span><span class="tag">${p.usage === "none" ? "no emoji" : "emoji " + p.usage}</span>${p.type === "reply" ? '<span class="tag">reply</span>' : ""}</td>
    <td class="n">${pct(p.rate)}</td><td class="n">${p.like.toLocaleString("en")}</td><td class="n">${p.view.toLocaleString("en")}</td></tr>`).join("")
    || '<tr><td colspan="5" class="empty">No post matches these filters.</td></tr>';
  $("more").hidden = state.shown >= posts.length;
}

function set(key, value) { state[key] = value; if (key !== "shown") state.shown = 25; render(); }
$("brand").addEventListener("click", e => {
  if (!e.target.dataset.v) return;
  [...$("brand").children].forEach(b => b.setAttribute("aria-pressed", b === e.target));
  set("brand", e.target.dataset.v);
});
["type", "topic", "emoji", "tone", "sort"].forEach(id => $(id).addEventListener("change", e => set(id, e.target.value)));
$("more").addEventListener("click", () => set("shown", state.shown + 25));
$("reset").addEventListener("click", () => {
  Object.assign(state, { brand: "both", type: "original", topic: "all", emoji: "all", tone: "all", sort: "high", shown: 25 });
  ["type", "topic", "emoji", "tone", "sort"].forEach(id => $(id).value = state[id]);
  [...$("brand").children].forEach(b => b.setAttribute("aria-pressed", b.dataset.v === "both"));
  render();
});
render();
</script>
</body>
</html>
"""

out = ROOT / "outputs" / "explorer.html"
out.write_text(HTML.replace("/*DATA*/", data), encoding="utf-8")
print(f"Saved outputs/explorer.html ({len(posts)} posts, {out.stat().st_size / 1024:.0f} KB)")
