"""Reruns the day-trader pipeline (PAPER ONLY, nothing is ever ordered) and rebuilds dashboard.html.
Scan -> news -> entry -> stop/target -> time machine. Uses live free Yahoo data."""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SK = os.path.join(os.path.expanduser("~"), ".claude", "skills")
SYMS = sys.argv[1] if len(sys.argv) > 1 else "TSLA,NVDA,SPY,QQQ"
os.chdir(HERE)
os.makedirs("trader", exist_ok=True)


def run(skill, script, *args, out=None):
    cmd = [sys.executable, os.path.join(SK, skill, script)] + list(args)
    print(">", skill, *args)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if out and r.stdout:
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(r.stdout)
    print((r.stdout or r.stderr).strip().splitlines()[-1:] or "")
    return r.returncode


# paper only: make sure the config says so
cfg = os.path.join("trader", "config.json")
try:
    c = json.load(open(cfg))
except (OSError, ValueError):
    c = json.load(open(os.path.join(SK, "trader-budget", "config.example.json")))
c["paper"] = True
json.dump(c, open(cfg, "w"), indent=2)

for f in ("entry.json", "plan.json", "timemachine.json", "news.json", "watchlist.json"):
    try:
        os.remove(os.path.join("trader", f))
    except OSError:
        pass

run("trader-scanner", "scan.py", "orb", "--symbols", SYMS)
try:
    hits = json.load(open(os.path.join("trader", "watchlist.json")))["hits"]
except (OSError, ValueError, KeyError):
    hits = []
if hits:
    best = max(hits, key=lambda h: h.get("pct_over", 0))["symbol"]
    run("trader-news", "news.py", "--tickers", best, "--hours", "48", "--no-sec", "--dry-run", "--json", out=os.path.join("trader", "news.json"))
    run("trader-entry", "entry.py", "check", best, "--write")
    if run("trader-exit", "exit.py", "plan", "--write") == 0:
        run("trader-timemachine", "timemachine.py", "run", "--write")
else:
    print("No opening-range setups right now, so there is no trade plan.")
subprocess.run([sys.executable, "build_dashboard.py"])
