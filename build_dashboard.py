"""Builds dashboard.html from the files in trader/. Standard library only.
Reads: watchlist.json, news.json, plan.json, timemachine.json. Missing files are shown as 'none'."""
import json, os, html, sys

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(HERE, "trader")
e = html.escape


def load(name):
    try:
        with open(os.path.join(T, name), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


wl, news, plan, tm = load("watchlist.json"), load("news.json"), load("plan.json"), load("timemachine.json")
saved = bool((wl or {}).get("offline") or (tm or {}).get("source") == "offline")
session = (plan or {}).get("date") or ((wl or {}).get("as_of") or "unknown")
if saved:
    banner = ("SAVED SESSION %s — the market data was not live. Offline copy of that day, "
              "supplied with the skill pack." % e(str(session)))
else:
    banner = "Data as of %s (free delayed Yahoo data)." % e(str((wl or {}).get("as_of", "unknown")))


def money(v):
    return "$%.2f" % v


# ---- setups
rows = ""
for h in (wl or {}).get("hits", []):
    rows += ("<tr><td class=sym>%s</td><td>%s</td><td>%s</td><td>%s – %s</td><td class=up>+%s%%</td></tr>" % (
        e(h["symbol"]), e(",".join(h.get("setups", []))), money(h["price"]),
        money(h.get("or_low", 0)), money(h.get("or_high", 0)), e(str(h.get("pct_over", "")))))
if not rows:
    rows = "<tr><td colspan=5 class=muted>No setups found.</td></tr>"
scan_note = ""
if wl:
    scan_note = "Scanned %s of %s requested charts · %s · %s" % (
        wl.get("scanned"), wl.get("universe"), e(str(wl.get("mode", "")).upper()), e(str(wl.get("as_of", ""))))

# ---- news
moves = "".join(
    "<div class=move><b>%s</b> %s <span class=%s>%+.2f%%</span> vs prior close %s%s</div>" % (
        e(m["ticker"]), money(m["price"]), "up" if m["pct"] >= 0 else "dn", m["pct"],
        money(m["prev_close"]), " · <b class=warn>MOVING</b>" if m.get("moving") else "")
    for m in (news or {}).get("moves", []))
items = ""
for it in ((news or {}).get("items") or [])[:6]:
    tags = "".join("<span class=tag>%s</span>" % e(t) for t in it.get("tags", []))
    items += "<li><a href=\"%s\" target=_blank rel=noopener>%s</a>%s<div class=muted>%s · %s</div></li>" % (
        e(it.get("link", "#")), e(it["title"]), tags, e(it.get("source", "")), e(it.get("time", "")[:16].replace("T", " ")) + " UTC")
if not items:
    items = "<li class=muted>No news items.</li>"

# ---- plan
if plan:
    plan_html = """<div class=grid3>
 <div class=box><div class=lbl>ENTRY</div><div class=big>%s</div><div class=muted>%s · %s</div></div>
 <div class="box dnb"><div class=lbl>STOP</div><div class="big dn">%s</div><div class=muted>%s</div></div>
 <div class="box upb"><div class=lbl>TARGET</div><div class="big up">%s</div><div class=muted>%s</div></div></div>
 <p class=muted>%s long · risk %s a share · reward:risk %s · flat by %s ET, no overnight hold.<br>%s</p>""" % (
        money(plan["entry"]), e(plan["entry_time"]), e(plan["date"]), money(plan["stop"]), e(plan.get("stop_label", "")),
        money(plan["target"]), e(plan.get("target_label", "")), e(plan["symbol"]), money(plan["risk_per_share"]),
        plan.get("reward_risk"), e(plan.get("flat_by", "15:55")), e(plan.get("note", "")))
else:
    plan_html = "<p class=muted>No trade plan (no setup triggered).</p>"

# ---- time machine
if tm and "mc" in tm:
    m = tm["mc"]
    h = tm.get("history") or {}
    hist = ("<b>Same rule on the last %s real sessions:</b> fired %s times, %s hit the target, %s hit the stop, %s ended neither; average R %+.3f." % (
        h.get("sessions"), h.get("triggered"), h.get("target"), h.get("stop"), h.get("close"), h.get("avg_R", 0))) if h else ""
    tm_html = """<div class=odds>
 <div class="odd upb"><div class=pct>%.1f%%</div><div>TARGET FIRST</div></div>
 <div class="odd dnb"><div class=pct>%.1f%%</div><div>STOP FIRST</div></div>
 <div class="odd"><div class=pct>%.1f%%</div><div>NEITHER BY CLOSE</div></div></div>
 <p class=muted>%s replays of the rest of the session · green at close %.1f%% · average R %+.3f · price at close: median %s, 90%% between %s and %s.<br>
 %s A simulation, not a prediction.</p>%s""" % (
        m["p_target"] * 100, m["p_stop"] * 100, m["p_neither"] * 100, "{:,}".format(m["replays"]),
        m["p_green"] * 100, m["avg_R"], money(m["median_close"]), money(m["p5_close"]), money(m["p95_close"]), hist, "")
    b = m.get("bands") or []
    if b:
        W, H = 600, 150
        lo = min(r[0] for r in b); hi = max(r[4] for r in b)
        lo = min(lo, tm["plan"]["stop"]); hi = max(hi, tm["plan"]["target"])
        X = lambda i: i * W / max(1, len(b) - 1)
        Y = lambda v: H - (v - lo) / (hi - lo) * H
        top = " ".join("%.1f,%.1f" % (X(i), Y(r[4])) for i, r in enumerate(b))
        bot = " ".join("%.1f,%.1f" % (X(i), Y(r[0])) for i, r in reversed(list(enumerate(b))))
        mid = " ".join("%.1f,%.1f" % (X(i), Y(r[2])) for i, r in enumerate(b))
        tm_html += ("<svg viewBox='0 0 %d %d' class=fan><polygon points='%s %s' fill='#2b6cb0' opacity='.35'/>"
                    "<polyline points='%s' fill=none stroke='#e2e8f0' stroke-width=2 />"
                    "<line x1=0 x2=%d y1=%.1f y2=%.1f stroke='#48bb78' stroke-dasharray='5 4'/>"
                    "<line x1=0 x2=%d y1=%.1f y2=%.1f stroke='#f56565' stroke-dasharray='5 4'/></svg>"
                    "<div class=muted>Fan chart: shaded = 90%% of replays, white = median. Green line = target, red line = stop.</div>") % (
            W, H, top, bot, mid, W, Y(tm["plan"]["target"]), Y(tm["plan"]["target"]), W, Y(tm["plan"]["stop"]), Y(tm["plan"]["stop"]))
else:
    tm_html = "<p class=muted>No time machine result.</p>"

page = """<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Trader Desk</title><style>
:root{--bg:#0b0f17;--panel:#131a26;--line:#233047;--tx:#e2e8f0;--mu:#8795ab;--up:#48bb78;--dn:#f56565;--wa:#ecc94b}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font:15px/1.5 system-ui,Segoe UI,sans-serif}
.paper{background:#7b2d12;color:#fff;text-align:center;font-weight:800;letter-spacing:.12em;padding:12px 16px;border-bottom:3px solid var(--wa)}
.src{background:#1a2233;color:var(--wa);text-align:center;padding:8px 16px;font-size:13px}
main{max-width:1000px;margin:0 auto;padding:20px 16px 40px}
h1{font-size:20px;margin:6px 0 16px;letter-spacing:.05em}h2{font-size:13px;color:var(--mu);letter-spacing:.14em;margin:0 0 12px;text-transform:uppercase}
section{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:18px;margin-bottom:16px}
.odds{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.odd{border:1px solid var(--line);border-radius:10px;padding:16px;text-align:center;font-size:12px;letter-spacing:.1em;color:var(--mu)}
.pct{font-size:clamp(34px,8vw,64px);font-weight:800;color:var(--tx);line-height:1.1}.upb .pct{color:var(--up)}.dnb .pct{color:var(--dn)}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.box{border:1px solid var(--line);border-radius:10px;padding:14px}
.lbl{font-size:12px;letter-spacing:.14em;color:var(--mu)}.big{font-size:30px;font-weight:700}
.up{color:var(--up)}.dn{color:var(--dn)}.warn{color:var(--wa)}.muted{color:var(--mu);font-size:13px}
table{width:100%%;border-collapse:collapse}th,td{text-align:left;padding:8px 6px;border-bottom:1px solid var(--line)}th{color:var(--mu);font-size:12px;letter-spacing:.1em}
.sym{font-weight:700}ul{list-style:none;padding:0;margin:8px 0 0}li{padding:9px 0;border-bottom:1px solid var(--line)}a{color:#90cdf4;text-decoration:none}a:hover{text-decoration:underline}
.tag{background:#2d3748;color:var(--wa);font-size:11px;border-radius:4px;padding:1px 6px;margin-left:8px}.move{margin-bottom:6px}
.fan{width:100%%;height:auto;margin-top:12px;background:#0e1420;border-radius:8px}
@media(max-width:640px){.odds,.grid3{grid-template-columns:1fr}}
</style></head><body>
<div class=paper>PAPER ONLY — NOT REAL TRADES</div>
<div class=src>%(banner)s</div>
<main><h1>TRADER DESK · %(sym)s</h1>
<section><h2>Time machine odds</h2>%(tm)s</section>
<section><h2>Trade plan</h2>%(plan)s</section>
<section><h2>Setups the scanner found</h2><table><tr><th>TICKER</th><th>SETUP</th><th>PRICE</th><th>OPENING RANGE</th><th>OVER HIGH</th></tr>%(rows)s</table><p class=muted>%(scan)s</p></section>
<section><h2>Top news</h2>%(moves)s<ul>%(items)s</ul><p class=muted>Headlines are leads, not facts. Not financial advice.</p></section>
</main></body></html>""" % dict(
    banner=banner, sym=e((plan or {}).get("symbol", "")), tm=tm_html, plan=plan_html,
    rows=rows, scan=scan_note, moves=moves, items=items)

out = os.path.join(HERE, "dashboard.html")
with open(out, "w", encoding="utf-8") as fh:
    fh.write(page)
print("Wrote", out)
