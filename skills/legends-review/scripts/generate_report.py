#!/usr/bin/env python3
"""Render legends-review report.json files into an actionable, self-contained HTML report.

Usage: generate_report.py report.json [more.json ...] [-o report.html] [--lang en|fr] [--no-md]

One JSON -> individual report (one persona) or consensus report (legends).
Several JSONs -> merged report: reviewers are combined, findings renumbered.
Output is written NEXT TO the first report.json (never in the cwd) unless -o is given.
A diffable report.md lands next to the HTML unless --no-md.

The HTML is a standalone document (inline CSS/JS, no external requests) with:
severity/reviewer/category filters, a per-finding done-checklist persisted in
localStorage, a "copy fix prompt" button per finding (paste into Claude Code),
and a markdown export of the remaining findings. Light/dark theme.
"""
import argparse
import hashlib
import html
import json
import sys
from pathlib import Path

SEVERITIES = ["critical", "major", "minor", "info"]

LABELS = {
    "en": {
        "review": "Code review", "consensus": "Consensus", "average": "Average",
        "findings": "Findings", "actions": "Action plan", "praise": "What's genuinely good",
        "agreements": "Where they agreed", "disagreements": "Where they fought",
        "hard_truths": "The hard truths", "addressed": "addressed", "hide_done": "Hide done",
        "copy_md": "Copy remaining as Markdown", "copy_fix": "Copy fix prompt",
        "copied": "Copied!", "all": "All", "effort": "effort", "resolution": "Resolution",
        "champion": "championed by", "supported": "supported by",
        "severity": {"critical": "Critical", "major": "Major", "minor": "Minor", "info": "Info"},
        "method": "Generated from report.json by legends-review — data lives in the JSON, "
                  "the HTML is always regenerated, never edited by hand.",
        "remaining_title": "Code review follow-ups",
        "fix_intro": "Fix this code review finding:",
        "fix_outro": "Implement the fix, keep the change minimal, and verify with the project's tests.",
    },
    "fr": {
        "review": "Revue de code", "consensus": "Consensus", "average": "Moyenne",
        "findings": "Constats", "actions": "Plan d'action", "praise": "Ce qui est réussi",
        "agreements": "Là où ils sont d'accord", "disagreements": "Là où ils se sont battus",
        "hard_truths": "Les vérités qui dérangent", "addressed": "traités", "hide_done": "Masquer les faits",
        "copy_md": "Copier le restant en Markdown", "copy_fix": "Copier le prompt de fix",
        "copied": "Copié !", "all": "Tous", "effort": "effort", "resolution": "Résolution",
        "champion": "porté par", "supported": "soutenu par",
        "severity": {"critical": "Critique", "major": "Majeur", "minor": "Mineur", "info": "Info"},
        "method": "Généré depuis report.json par legends-review — les données vivent dans le JSON, "
                  "le HTML est toujours régénéré, jamais édité à la main.",
        "remaining_title": "Suivis de revue de code",
        "fix_intro": "Corrige ce constat de revue de code :",
        "fix_outro": "Implémente le fix, garde le changement minimal, et vérifie avec les tests du projet.",
    },
}

PALETTE_LIGHT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
PALETTE_DARK = ["#3987e5", "#d95926", "#199e70", "#c98500"]


def esc(s):
    return html.escape(str(s), quote=True)


def die(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def load(path):
    try:
        r = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as e:
        die(f"{path}: {e}")
    for field in ("date", "repo", "reviewers", "findings"):
        if field not in r:
            die(f"{path}: missing required field '{field}'")
    for f in r["findings"]:
        for field in ("id", "reviewer", "severity", "title", "description", "recommendation"):
            if field not in f:
                die(f"{path}: finding {f.get('id', '?')} missing '{field}'")
        if f["severity"] not in SEVERITIES:
            die(f"{path}: finding {f['id']} has invalid severity '{f['severity']}' "
                f"(expected one of {', '.join(SEVERITIES)})")
    return r


def merge(reports):
    if len(reports) == 1:
        return reports[0]
    base = dict(reports[0])
    seen = set()
    reviewers, findings, actions, praise = [], [], [], []
    for r in reports:
        for rv in r["reviewers"]:
            if rv["id"] in seen:
                die(f"duplicate reviewer '{rv['id']}' across merged reports — "
                    "merge is for combining different personas' reviews of the same change")
            seen.add(rv["id"])
            reviewers.append(rv)
        findings.extend(r["findings"])
        actions.extend(r.get("actions", []))
        praise.extend(r.get("praise", []))
    for i, f in enumerate(findings, 1):
        f["id"] = i
    actions.sort(key=lambda a: a.get("rank", 99))
    for i, a in enumerate(actions, 1):
        a["rank"] = i
    base.update(reviewers=reviewers, findings=findings, actions=actions, praise=praise)
    base["review_type"] = "merged"
    base.pop("consensus", None)
    return base


def overall_rating(r):
    if r.get("consensus", {}).get("rating") is not None:
        return r["consensus"]["rating"], True
    ratings = [rv["rating"] for rv in r["reviewers"] if rv.get("rating") is not None]
    if not ratings:
        return None, False
    return round(sum(ratings) / len(ratings), 1), False


def report_id(r):
    key = f'{r["repo"]}|{r["date"]}|{"+".join(sorted(rv["id"] for rv in r["reviewers"]))}'
    return hashlib.sha1(key.encode()).hexdigest()[:10]


def sort_findings(findings):
    return sorted(findings, key=lambda f: (SEVERITIES.index(f["severity"]), f["id"]))


def reviewer_by_id(r, rid):
    return next((rv for rv in r["reviewers"] if rv["id"] == rid), {"name": rid, "emoji": ""})


def action_done(r, a):
    """An action is done when explicitly resolved, else when all its finding_ids are resolved."""
    if "resolved" in a:
        return bool(a["resolved"])
    ids = a.get("finding_ids") or []
    by_id = {f.get("id"): f for f in r.get("findings", [])}
    return bool(ids) and all(by_id.get(i, {}).get("resolved") for i in ids)


def finding_card(f, r, L):
    rv = reviewer_by_id(r, f["reviewer"])
    loc = ""
    if f.get("file"):
        loc = f'<code class="loc">{esc(f["file"])}{":" + str(f["line"]) if f.get("line") else ""}</code>'
    agreed = "".join(f'<span class="rv-tag" title="{esc(reviewer_by_id(r, a)["name"])}">'
                     f'{esc(reviewer_by_id(r, a)["emoji"])}</span>' for a in f.get("agreed_by", []))
    fix = (f'<pre class="fix">{esc(f["fix_hint"])}</pre>' if f.get("fix_hint") else "")
    effort = f'<span class="eff">{esc(f["effort"])}</span>' if f.get("effort") else ""
    cat = f'<span class="cat">{esc(f["category"])}</span>' if f.get("category") else ""
    return f"""<details class="finding" data-id="{f["id"]}" data-severity="{esc(f["severity"])}"
 data-reviewer="{esc(f["reviewer"])}" data-category="{esc(f.get("category", ""))}"
 data-resolved="{1 if f.get("resolved") else 0}">
<summary>
<input type="checkbox" class="done-box" aria-label="done" onclick="event.stopPropagation()">
<span class="sev sev-{esc(f["severity"])}">{esc(L["severity"][f["severity"]])}</span>
<span class="f-title">{esc(f["title"])}</span>
{cat}{loc}
<span class="rv-tag" title="{esc(rv["name"])}">{esc(rv.get("emoji", ""))}</span>{agreed}{effort}
</summary>
<div class="f-body">
<p>{esc(f["description"])}</p>
<p class="rec"><strong>→</strong> {esc(f["recommendation"])}</p>
{fix}
<button class="btn copy-fix" data-id="{f["id"]}">{esc(L["copy_fix"])}</button>
</div>
</details>"""


def render_html(r, lang):
    L = LABELS[lang]
    rating, is_consensus = overall_rating(r)
    rid = report_id(r)
    findings = sort_findings(r["findings"])
    sev_counts = {s: sum(1 for f in findings if f["severity"] == s) for s in SEVERITIES}
    categories = sorted({f["category"] for f in findings if f.get("category")})

    where = " · ".join(x for x in [
        esc(r["repo"]),
        esc(r.get("branch", "")) + ("@" + esc(r["commit"]) if r.get("commit") else ""),
        esc(r["date"])] if x)

    cards = "".join(f"""<div class="tile reviewer">
<div class="v">{esc(rv.get("emoji", ""))} {rv["rating"] if rv.get("rating") is not None else "—"}<small>/10</small></div>
<div class="l">{esc(rv["name"])}</div>
<p class="verdict">“{esc(rv.get("verdict", ""))}”</p>
</div>""" for rv in r["reviewers"])

    rating_tile = ""
    if rating is not None and len(r["reviewers"]) > 1:
        label = L["consensus"] if is_consensus else L["average"]
        rating_tile = (f'<div class="tile consensus"><div class="v">{rating}<small>/10</small></div>'
                       f'<div class="l">{esc(label)}</div></div>')

    consensus_html = ""
    c = r.get("consensus", {})
    if c.get("agreements") or c.get("disagreements"):
        ag = "".join(f"<li>{esc(a)}</li>" for a in c.get("agreements", []))
        dg = "".join(
            f'<li><strong>{esc(d["topic"])}</strong> — {esc(d.get("resolution", ""))}</li>'
            for d in c.get("disagreements", []))
        consensus_html = f"""<div class="grid2">
<div class="card"><h2>{esc(L["agreements"])}</h2><ul class="value">{ag}</ul></div>
<div class="card"><h2>{esc(L["disagreements"])}</h2><ul class="value">{dg}</ul></div>
</div>"""

    truths = [(rv, rv["hard_truth"]) for rv in r["reviewers"] if rv.get("hard_truth")]
    truths_html = ""
    if truths:
        items = "".join(f'<li>{esc(rv.get("emoji", ""))} <em>“{esc(t)}”</em>'
                        f' <span class="who">— {esc(rv["name"])}</span></li>' for rv, t in truths)
        truths_html = f'<div class="card"><h2>{esc(L["hard_truths"])}</h2><ul class="value truths">{items}</ul></div>'

    sev_chips = "".join(
        f'<button class="chip on" data-filter="severity" data-value="{s}">'
        f'<span class="dot sev-{s}"></span>{esc(L["severity"][s])} <b>{sev_counts[s]}</b></button>'
        for s in SEVERITIES if sev_counts[s])
    rv_chips = "".join(
        f'<button class="chip on" data-filter="reviewer" data-value="{esc(rv["id"])}">'
        f'{esc(rv.get("emoji", ""))} {esc(rv["name"].split()[0])}</button>'
        for rv in r["reviewers"]) if len(r["reviewers"]) > 1 else ""
    cat_select = ""
    if categories:
        opts = "".join(f'<option value="{esc(c)}">{esc(c)}</option>' for c in categories)
        cat_select = f'<select id="cat"><option value="">{esc(L["all"])}</option>{opts}</select>'

    findings_html = "".join(finding_card(f, r, L) for f in findings)

    actions_html = ""
    if r.get("actions"):
        items = "".join(
            ('<li class="done">' if action_done(r, a) else "<li>")
            + '<span class="box' + (" done" if action_done(r, a) else "")
            + '" aria-hidden="true">' + ("✓" if action_done(r, a) else "") + "</span><span>"
            + esc(a["title"])
            + (f' <span class="who">— {esc(L["champion"])} {esc(reviewer_by_id(r, a["champion"])["name"])}'
               + (f', {esc(L["supported"])} '
                  + ", ".join(esc(reviewer_by_id(r, s)["name"]) for s in a["supported_by"])
                  if a.get("supported_by") else "")
               + "</span>" if a.get("champion") else "")
            + f'</span><span class="eff">{esc(a.get("effort", "—"))}</span></li>'
            for a in sorted(r["actions"], key=lambda a: a.get("rank", 99)))
        actions_html = f'<div class="card"><h2>{esc(L["actions"])}</h2><ul class="steps">{items}</ul></div>'

    praise_html = ""
    if r.get("praise"):
        items = "".join(f"<li>{esc(p)}</li>" for p in r["praise"])
        praise_html = f'<div class="card"><h2>{esc(L["praise"])}</h2><ul class="value">{items}</ul></div>'

    css_vars_light = "".join(f"--s{i + 1}: {c};" for i, c in enumerate(PALETTE_LIGHT))
    css_vars_dark = "".join(f"--s{i + 1}: {c};" for i, c in enumerate(PALETTE_DARK))
    dark_vars = ("color-scheme: dark; --plane:#0d0d0d; --surface:#1a1a19; --ink:#fff; --ink-2:#c3c2b7;"
                 " --muted:#898781; --grid:#2c2c2a; --axis:#383835; --ring:rgba(255,255,255,0.10);"
                 f" {css_vars_dark} --good-text:#0ca30c; --crit:#ef5350;")

    data = {
        "reportId": rid, "lang": lang, "repo": r["repo"], "branch": r.get("branch", ""),
        "commit": r.get("commit", ""), "date": r["date"],
        "labels": {"fix_intro": L["fix_intro"], "fix_outro": L["fix_outro"],
                   "remaining_title": L["remaining_title"], "copied": L["copied"]},
        "reviewers": {rv["id"]: {"name": rv["name"], "emoji": rv.get("emoji", "")} for rv in r["reviewers"]},
        "findings": [{k: f.get(k) for k in ("id", "reviewer", "severity", "category", "title",
                                            "file", "line", "description", "recommendation",
                                            "fix_hint", "effort")} for f in findings],
        "actions": [{"rank": a.get("rank"), "title": a["title"], "effort": a.get("effort"),
                     "done": action_done(r, a)}
                    for a in r.get("actions", [])],
    }
    data_json = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")

    title = f'{L["review"]} {r["repo"]} — {r["date"]}'
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<style>
  :root {{ color-scheme: light; --plane:#f9f9f7; --surface:#fcfcfb; --ink:#0b0b0b; --ink-2:#52514e;
    --muted:#898781; --grid:#e1e0d9; --axis:#c3c2b7; --ring:rgba(11,11,11,0.10);
    {css_vars_light} --good-text:#006300; --crit:#c62828; }}
  @media (prefers-color-scheme: dark) {{ :root:where(:not([data-theme="light"])) {{ {dark_vars} }} }}
  :root[data-theme="dark"] {{ {dark_vars} }}
  body {{ margin:0; background:var(--plane); color:var(--ink); font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif; }}
  .wrap {{ max-width:980px; margin:0 auto; padding:32px 20px 64px; display:grid; gap:20px; }}
  .eyebrow {{ font-size:12px; text-transform:uppercase; letter-spacing:.08em; color:var(--muted); }}
  h1 {{ font-size:27px; font-weight:700; margin:4px 0 2px; text-wrap:balance; }}
  header p {{ color:var(--ink-2); max-width:70ch; margin:6px 0 0; }}
  .tiles {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:12px; }}
  .tile {{ background:var(--surface); border:1px solid var(--ring); border-radius:10px; padding:14px 16px; }}
  .tile .v {{ font-size:26px; font-weight:700; }} .tile .v small {{ font-size:14px; font-weight:600; color:var(--ink-2); }}
  .tile .l {{ font-size:12.5px; color:var(--ink-2); margin-top:2px; }}
  .tile .verdict {{ font-size:13px; color:var(--ink-2); margin:8px 0 0; font-style:italic; }}
  .tile.consensus {{ border-color:var(--s1); }}
  .card {{ background:var(--surface); border:1px solid var(--ring); border-radius:10px; padding:18px 20px; }}
  .card h2 {{ font-size:15px; font-weight:650; margin:0 0 10px; }}
  .grid2 {{ display:grid; grid-template-columns:1fr; gap:20px; }}
  @media (min-width:880px) {{ .grid2 {{ grid-template-columns:1fr 1fr; }} }}
  ul.value {{ margin:0; padding-left:1.1em; display:grid; gap:8px; color:var(--ink-2); }}
  ul.value .who {{ color:var(--muted); font-size:12.5px; }}
  .progress {{ display:flex; align-items:center; gap:12px; }}
  .progress .bar {{ flex:1; height:8px; background:var(--grid); border-radius:99px; overflow:hidden; }}
  .progress .bar > div {{ height:100%; width:0; background:var(--s3); border-radius:99px; transition:width .2s; }}
  .progress .num {{ font-variant-numeric:tabular-nums; font-size:13px; color:var(--ink-2); white-space:nowrap; }}
  .filters {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; }}
  .chip {{ display:inline-flex; align-items:center; gap:6px; font:12.5px system-ui; padding:4px 11px;
    border-radius:999px; border:1px solid var(--axis); background:none; color:var(--muted); cursor:pointer; }}
  .chip.on {{ color:var(--ink); border-color:var(--ink-2); background:var(--surface); }}
  .chip b {{ font-variant-numeric:tabular-nums; }}
  .chip .dot {{ width:9px; height:9px; border-radius:99px; display:inline-block; }}
  select {{ font:12.5px system-ui; padding:4px 8px; border-radius:7px; border:1px solid var(--axis);
    background:var(--surface); color:var(--ink); }}
  .sev {{ font-size:10.5px; font-weight:700; text-transform:uppercase; letter-spacing:.05em;
    padding:2px 8px; border-radius:99px; color:#fff; white-space:nowrap; }}
  .sev-critical {{ background:var(--crit); }} .sev-major {{ background:var(--s2); }}
  .sev-minor {{ background:var(--s4); }} .sev-info {{ background:var(--s1); }}
  .dot.sev-critical {{ background:var(--crit); }} .dot.sev-major {{ background:var(--s2); }}
  .dot.sev-minor {{ background:var(--s4); }} .dot.sev-info {{ background:var(--s1); }}
  .finding {{ background:var(--surface); border:1px solid var(--ring); border-radius:10px; margin-bottom:8px; }}
  .finding.hidden {{ display:none; }}
  .finding summary {{ display:flex; align-items:center; gap:9px; padding:10px 14px; cursor:pointer;
    flex-wrap:wrap; list-style:none; }}
  .finding summary::-webkit-details-marker {{ display:none; }}
  .finding .f-title {{ font-weight:600; flex:1; min-width:200px; }}
  .finding.done .f-title {{ text-decoration:line-through; color:var(--muted); font-weight:400; }}
  .finding .cat {{ font-size:11px; color:var(--muted); border:1px solid var(--grid); border-radius:5px; padding:1px 6px; }}
  .finding .loc {{ font-family:ui-monospace,monospace; font-size:11.5px; color:var(--muted); }}
  .finding .rv-tag {{ font-size:13px; }}
  .eff {{ font-family:ui-monospace,monospace; font-size:12px; color:var(--muted); white-space:nowrap; }}
  .f-body {{ padding:2px 16px 14px 42px; color:var(--ink-2); font-size:14px; }}
  .f-body p {{ margin:6px 0; max-width:75ch; }}
  .f-body .rec strong {{ color:var(--good-text); }}
  pre.fix {{ background:var(--plane); border:1px solid var(--grid); border-radius:8px; padding:10px 12px;
    font-size:12.5px; overflow-x:auto; }}
  .btn {{ font:12.5px system-ui; padding:5px 12px; border-radius:7px; border:1px solid var(--axis);
    background:var(--surface); color:var(--ink); cursor:pointer; margin-top:6px; }}
  .btn:hover {{ border-color:var(--ink-2); }}
  .done-box {{ width:16px; height:16px; accent-color:var(--s3); flex-shrink:0; }}
  ul.steps {{ margin:0; padding:0; list-style:none; display:grid; gap:9px; }}
  ul.steps li {{ display:grid; grid-template-columns:24px 1fr auto; gap:10px; align-items:baseline;
    font-size:14px; border-top:1px solid var(--grid); padding-top:9px; }}
  ul.steps li:first-child {{ border-top:0; padding-top:0; }}
  ul.steps .box {{ width:15px; height:15px; border:1.6px solid var(--axis); border-radius:4px; margin-top:2px; }}
  ul.steps .box.done {{ background:var(--s3); border-color:var(--s3); color:#fff; font-size:11px;
    line-height:15px; text-align:center; font-weight:700; }}
  ul.steps li.done > span:nth-child(2) {{ text-decoration:line-through; color:var(--muted); }}
  ul.steps .who {{ color:var(--muted); font-size:12.5px; }}
  footer {{ font-size:12.5px; color:var(--muted); max-width:78ch; }}
  #toast {{ position:fixed; bottom:24px; left:50%; transform:translateX(-50%); background:var(--ink);
    color:var(--plane); font-size:13px; padding:8px 16px; border-radius:8px; opacity:0; transition:opacity .15s; }}
</style>
</head>
<body data-report-id="{rid}">
<div class="wrap">
  <header>
    <div class="eyebrow">{L["review"]} · {where}</div>
    <h1>{esc(r.get("change_summary", r["repo"]))}</h1>
    {f'<p>{esc(r["scope"])}</p>' if r.get("scope") else ""}
  </header>
  <div class="tiles">{rating_tile}{cards}</div>
  {consensus_html}
  <div class="card">
    <h2>{esc(L["findings"])}</h2>
    <div class="progress"><div class="bar"><div id="pbar"></div></div>
      <span class="num"><span id="pdone">0</span>/{len(findings)} {esc(L["addressed"])}</span></div>
    <div class="filters" style="margin:12px 0 14px">
      {sev_chips}{rv_chips}{cat_select}
      <button class="chip" id="hide-done">{esc(L["hide_done"])}</button>
      <button class="chip" id="export-md">{esc(L["copy_md"])}</button>
    </div>
    <div id="findings">{findings_html}</div>
  </div>
  {actions_html}
  {truths_html}
  {praise_html}
  <footer><p>{esc(L["method"])}</p></footer>
</div>
<div id="toast" role="status"></div>
<script type="application/json" id="data">{data_json}</script>
<script>
const DATA = JSON.parse(document.getElementById('data').textContent);
const KEY = 'legends-review:' + DATA.reportId;
const state = JSON.parse(localStorage.getItem(KEY) || '{{}}');
const findings = [...document.querySelectorAll('.finding')];
const toast = document.getElementById('toast');
let hideDone = false;

function notify(msg) {{
  toast.textContent = msg; toast.style.opacity = '1';
  setTimeout(() => toast.style.opacity = '0', 1400);
}}
function copyText(text, msg) {{
  const done = () => notify(msg || DATA.labels.copied);
  if (navigator.clipboard) navigator.clipboard.writeText(text).then(done, () => fallback());
  else fallback();
  function fallback() {{
    const ta = document.createElement('textarea');
    ta.value = text; document.body.appendChild(ta); ta.select();
    document.execCommand('copy'); ta.remove(); done();
  }}
}}
function refresh() {{
  const sevOn = new Set([...document.querySelectorAll('.chip.on[data-filter="severity"]')].map(c => c.dataset.value));
  const rvChips = [...document.querySelectorAll('.chip[data-filter="reviewer"]')];
  const rvOn = new Set(rvChips.filter(c => c.classList.contains('on')).map(c => c.dataset.value));
  const cat = document.getElementById('cat') ? document.getElementById('cat').value : '';
  let done = 0;
  findings.forEach(el => {{
    const isDone = el.dataset.id in state ? !!state[el.dataset.id] : el.dataset.resolved === '1';
    el.classList.toggle('done', isDone);
    el.querySelector('.done-box').checked = isDone;
    if (isDone) done++;
    const visible = sevOn.has(el.dataset.severity)
      && (!rvChips.length || rvOn.has(el.dataset.reviewer))
      && (!cat || el.dataset.category === cat)
      && !(hideDone && isDone);
    el.classList.toggle('hidden', !visible);
  }});
  document.getElementById('pdone').textContent = done;
  document.getElementById('pbar').style.width = (findings.length ? 100 * done / findings.length : 0) + '%';
}}
findings.forEach(el => el.querySelector('.done-box').addEventListener('change', e => {{
  state[el.dataset.id] = e.target.checked;
  localStorage.setItem(KEY, JSON.stringify(state));
  refresh();
}}));
document.querySelectorAll('.chip[data-filter]').forEach(c =>
  c.addEventListener('click', () => {{ c.classList.toggle('on'); refresh(); }}));
const catSel = document.getElementById('cat');
if (catSel) catSel.addEventListener('change', refresh);
document.getElementById('hide-done').addEventListener('click', e => {{
  hideDone = !hideDone; e.target.classList.toggle('on', hideDone); refresh();
}});
function fixPrompt(f) {{
  const rv = DATA.reviewers[f.reviewer] || {{name: f.reviewer}};
  const loc = f.file ? f.file + (f.line ? ':' + f.line : '') : '';
  return [DATA.labels.fix_intro, '',
    'Repo: ' + DATA.repo + (DATA.branch ? ' (' + DATA.branch + (DATA.commit ? '@' + DATA.commit : '') + ')' : ''),
    loc ? 'File: ' + loc : null,
    'Severity: ' + f.severity + (f.category ? ' - Category: ' + f.category : '') + ' - ' + rv.name + ' review',
    'Finding: ' + f.title, '', f.description, '',
    'Recommended fix: ' + f.recommendation,
    f.fix_hint ? '\\n' + f.fix_hint : null,
    '', DATA.labels.fix_outro].filter(x => x !== null).join('\\n');
}}
document.querySelectorAll('.copy-fix').forEach(b => b.addEventListener('click', () => {{
  const f = DATA.findings.find(x => String(x.id) === b.dataset.id);
  copyText(fixPrompt(f));
}}));
document.getElementById('export-md').addEventListener('click', () => {{
  const remaining = DATA.findings.filter(f => !state[f.id]);
  const bySev = {{}};
  remaining.forEach(f => (bySev[f.severity] = bySev[f.severity] || []).push(f));
  const lines = ['# ' + DATA.labels.remaining_title + ' — ' + DATA.repo + ' (' + DATA.date + ')', ''];
  ['critical', 'major', 'minor', 'info'].forEach(s => {{
    if (!bySev[s]) return;
    lines.push('## ' + s.charAt(0).toUpperCase() + s.slice(1), '');
    bySev[s].forEach(f => {{
      const loc = f.file ? ' — `' + f.file + (f.line ? ':' + f.line : '') + '`' : '';
      lines.push('- [ ] **' + f.title + '**' + loc + (f.effort ? ' (' + f.effort + ')' : ''));
      lines.push('  ' + f.recommendation);
    }});
    lines.push('');
  }});
  if (DATA.actions.length) {{
    lines.push('## Actions', '');
    DATA.actions.forEach(a => lines.push((a.rank || '-') + '. [' + (a.done ? 'x' : ' ') + '] ' + a.title + (a.effort ? ' (' + a.effort + ')' : '')));
  }}
  copyText(lines.join('\\n'));
}});
refresh();
</script>
</body>
</html>
"""


def render_md(r, lang):
    L = LABELS[lang]
    rating, is_consensus = overall_rating(r)
    lines = [f'# {L["review"]} — {r["repo"]} ({r["date"]})', ""]
    meta = [x for x in [r.get("branch", ""), r.get("commit", "")] if x]
    if meta:
        lines += [f'**{" @ ".join(meta)}**', ""]
    if r.get("change_summary"):
        lines += [r["change_summary"], ""]
    lines.append("| Reviewer | Rating | Verdict |")
    lines.append("|---|---|---|")
    for rv in r["reviewers"]:
        rating_s = f'{rv["rating"]}/10' if rv.get("rating") is not None else "—"
        lines.append(f'| {rv.get("emoji", "")} {rv["name"]} | {rating_s} | {rv.get("verdict", "")} |')
    if rating is not None and len(r["reviewers"]) > 1:
        label = L["consensus"] if is_consensus else L["average"]
        lines += ["", f"**{label} : {rating}/10**"]
    lines += ["", f'## {L["findings"]}', ""]
    for s in SEVERITIES:
        group = [f for f in sort_findings(r["findings"]) if f["severity"] == s]
        if not group:
            continue
        lines.append(f'### {L["severity"][s]}')
        for f in group:
            loc = f' — `{f["file"]}{":" + str(f["line"]) if f.get("line") else ""}`' if f.get("file") else ""
            eff = f' ({f["effort"]})' if f.get("effort") else ""
            lines.append(f'- [{"x" if f.get("resolved") else " "}] **{f["title"]}**{loc}{eff}')
            lines.append(f'  {f["recommendation"]}')
        lines.append("")
    if r.get("actions"):
        lines += [f'## {L["actions"]}', ""]
        for a in sorted(r["actions"], key=lambda a: a.get("rank", 99)):
            eff = f' ({a["effort"]})' if a.get("effort") else ""
            lines.append(f'{a.get("rank", "-")}. [{"x" if action_done(r, a) else " "}] {a["title"]}{eff}')
        lines.append("")
    lines.append(f'---\n{L["method"]}')
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("report_json", nargs="+")
    ap.add_argument("-o", "--output", default=None,
                    help="default: report.html next to the first report.json (never the cwd)")
    ap.add_argument("--lang", choices=("en", "fr"), default="en")
    ap.add_argument("--no-md", action="store_true", help="skip the diffable report.md")
    args = ap.parse_args()
    r = merge([load(p) for p in args.report_json])
    output = Path(args.output) if args.output else Path(args.report_json[0]).resolve().parent / "report.html"
    output.write_text(render_html(r, args.lang))
    print(f"OK {output}", file=sys.stderr)
    if not args.no_md:
        md = output.with_suffix(".md")
        md.write_text(render_md(r, args.lang))
        print(f"OK {md}", file=sys.stderr)


if __name__ == "__main__":
    main()
