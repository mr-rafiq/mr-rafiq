#!/usr/bin/env python3
"""Render profile artwork from public GitHub data. Python standard library only."""
from datetime import date, datetime, timedelta, timezone
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import json
import os
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
USER = "mr-rafiq"
BG, PANEL, BORDER = "#0b111b", "#101b29", "#233447"
WHITE, MUTED, TEAL, GOLD = "#edf4fa", "#93a8bd", "#55e6c1", "#f2bf76"


def fetch(url, api=False):
    headers = {"User-Agent": "mr-rafiq-profile", "Accept": "application/vnd.github+json" if api else "text/html"}
    if api and os.getenv("GH_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GH_TOKEN"]
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=45) as response:
        raw = response.read().decode("utf-8")
    return json.loads(raw) if api else raw


class Calendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells, self.counts = {}, {}
        self.tip, self.buffer = None, ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "data-date" in attrs and "data-level" in attrs:
            self.cells[attrs["id"]] = (attrs["data-date"], int(attrs["data-level"]))
        if tag == "tool-tip":
            self.tip, self.buffer = attrs.get("for"), ""

    def handle_data(self, value):
        if self.tip:
            self.buffer += value

    def handle_endtag(self, tag):
        if tag == "tool-tip" and self.tip:
            text = self.buffer.strip()
            match = re.search(r"^([\d,]+) contributions? on ", text)
            if match:
                self.counts[self.tip] = int(match.group(1).replace(",", ""))
            elif text.startswith("No contributions on "):
                self.counts[self.tip] = 0
            self.tip = None

    def days(self):
        if not self.cells or any(key not in self.counts for key in self.cells):
            raise ValueError("GitHub contribution markup changed; keeping existing artwork")
        return {day: {"date": day, "level": level, "count": self.counts[key]}
                for key, (day, level) in self.cells.items()}


def text(x, y, value, size=14, fill=WHITE, extra=""):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" {extra}>{escape(str(value))}</text>'


def card(width, height, title, body, description):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">'
            f'<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>'
            '<style>text{font-family:ui-monospace,SFMono-Regular,Consolas,"Liberation Mono",monospace}'
            '.reveal{animation:reveal .7s ease-out both}@keyframes reveal{from{opacity:.2}to{opacity:1}}'
            '@media(prefers-reduced-motion:reduce){.reveal{animation:none}}</style>'
            f'<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="18" fill="{BG}" stroke="{BORDER}"/>'
            f'<circle cx="26" cy="25" r="4" fill="#ff777b"/><circle cx="42" cy="25" r="4" fill="{GOLD}"/>'
            f'<circle cx="58" cy="25" r="4" fill="{TEAL}"/>' + body + '</svg>\n')


def render(profile, repos, days, today):
    contributions = sum(day["count"] for day in days)
    active = sum(day["count"] > 0 for day in days)
    longest = run = 0
    for day in days:
        run = run + 1 if day["count"] else 0
        longest = max(longest, run)
    current = 0
    end = len(days) - 1 if days[-1]["count"] else len(days) - 2
    for day in reversed(days[:end+1]):
        if not day["count"]:
            break
        current += 1
    original = [repo for repo in repos if not repo["fork"]]
    stars = sum(repo["stargazers_count"] for repo in original)
    snapshot = {"username": USER, "as_of": today.isoformat(), "window_start": days[0]["date"],
                "public_repositories": len(repos), "original_public_repositories": len(original),
                "stars_on_original_public_repositories": stars, "followers": profile["followers"],
                "contributions": contributions, "active_days": active,
                "current_streak_days": current, "longest_streak_days": longest, "days": days,
                "sources": [f"https://github.com/{USER}", f"https://api.github.com/users/{USER}/repos"]}
    body = text(82, 30, "~/mohamed-rafiq", 12, MUTED)
    body += text(30, 82, "MOHAMED RAFIQ", 36, WHITE, 'font-weight="700"')
    body += text(31, 114, "Full-stack development / AI / Computational design", 16, TEAL)
    body += text(31, 157, "Turning complex workflows into useful software.", 16)
    body += text(31, 188, "GERMANY  ·  RAFIQ.TECH  ·  @MR-RAFIQ", 12, MUTED)
    for i in range(6):
        body += f'<path d="M {785+i*13} 64 L {732+i*13} 172" stroke="{TEAL}" opacity="{.12+i*.1}" stroke-width="3"/>'
    hero = card(900, 216, "Mohamed Rafiq — Full-stack AI developer", body, "Germany. Full-stack development, AI, and computational design. rafiq.tech")

    body = text(82, 30, "contributions / trailing 365 days", 12, MUTED)
    body += text(30, 70, f"{contributions:,} contributions", 24, WHITE, 'font-weight="700"')
    body += text(30, 96, f'{days[0]["date"]} → {today.isoformat()}  ·  {active} active days', 12, MUTED)
    colors = ["#192738", "#164a49", "#1b8070", "#30b596", TEAL]
    start = date.fromisoformat(days[0]["date"])
    # GitHub columns start on Sunday.
    sunday = start - timedelta(days=(start.weekday()+1) % 7)
    seen_months = set()
    for i, day in enumerate(days):
        d = date.fromisoformat(day["date"])
        offset = (d-sunday).days
        col, row = offset//7, offset%7
        x, y = 51+col*15, 132+row*15
        month = (d.year, d.month)
        if month not in seen_months and d.day <= 7:
            body += text(x, 122, d.strftime("%b"), 10, MUTED)
            seen_months.add(month)
        body += (f'<rect class="reveal" x="{x}" y="{y}" width="11" height="11" rx="2" '
                 f'fill="{colors[day["level"]]}" style="animation-delay:{min(col*.012,.65):.3f}s">'
                 f'<title>{day["date"]}: {day["count"]} contributions</title></rect>')
    for label, row in [("M",1),("W",3),("F",5)]:
        body += text(29, 140+row*15, label, 10, MUTED)
    body += text(30, 263, "Public profile activity · refreshed daily", 11, MUTED)
    body += text(705, 263, "Less", 10, MUTED)
    for i, color in enumerate(colors):
        body += f'<rect x="{738+i*15}" y="253" width="11" height="11" rx="2" fill="{color}"/>'
    body += text(820, 263, "More", 10, MUTED)
    heatmap = card(900, 285, "mr-rafiq contribution calendar", body, f"{contributions} contributions in the 365 days ending {today}. {active} active days.")

    body = text(82, 30, "identity / whoami", 12, MUTED)
    monogram = ["███╗   ███╗ ██████╗ ", "████╗ ████║ ██╔══██╗", "██╔████╔██║ ██████╔╝", "██║╚██╔╝██║ ██╔══██╗", "██║ ╚═╝ ██║ ██║  ██║", "╚═╝     ╚═╝ ╚═╝  ╚═╝"]
    for i, line in enumerate(monogram):
        body += text(34, 87+i*23, line, 19, TEAL, 'xml:space="preserve"')
    body += text(30, 262, "Mohamed Rafiq", 22, WHITE, 'font-weight="700"')
    body += text(30, 294, "$ build useful things", 14, GOLD)
    body += text(30, 335, "Full-stack AI developer", 13)
    body += text(30, 360, "Computational design graduate", 13, MUTED)
    body += text(30, 385, "Germany · digital nomad", 13, MUTED)
    identity = card(440, 418, "Mohamed Rafiq — terminal identity", body, "MR terminal monogram. Full-stack AI developer, computational design graduate, based in Germany.")

    body = text(82, 30, "activity / github", 12, MUTED)
    stats = [("PUBLIC REPOS", len(repos)), ("FOLLOWERS", profile["followers"]),
             ("ACTIVE DAYS", active), ("365-DAY CONTRIBUTIONS", f"{contributions:,}")]
    for i, (label, value) in enumerate(stats):
        x, y = 30+(i%2)*205, 60+(i//2)*110
        body += f'<rect x="{x}" y="{y}" width="175" height="91" rx="9" fill="{PANEL}"/>'
        body += text(x+15, y+27, label, 10, MUTED)
        body += text(x+15, y+67, value, 32, TEAL, 'font-weight="700"')
    body += text(30, 308, f"Current streak    {current} {'day' if current == 1 else 'days'}", 14)
    body += text(30, 335, f"Longest streak    {longest} {'day' if longest == 1 else 'days'}", 14)
    body += text(30, 362, f"Original repos    {len(original)} · {stars} stars", 13, GOLD)
    body += text(30, 393, f"Updated {today.isoformat()} · public data", 11, MUTED)
    stats_svg = card(440, 418, "mr-rafiq GitHub activity", body, f"{len(repos)} public repositories, {profile['followers']} followers, {contributions} contributions. As of {today}.")
    return snapshot, {"hero.svg": hero, "contributions.svg": heatmap, "identity.svg": identity, "stats.svg": stats_svg}


def main():
    today = date.fromisoformat(os.getenv("PROFILE_DATE", datetime.now(timezone.utc).date().isoformat()))
    start = today-timedelta(days=364)
    calendar = {}
    for year in range(start.year, today.year+1):
        parser = Calendar()
        parser.feed(fetch(f"https://github.com/users/{USER}/contributions?from={year}-01-01&to={year}-12-31"))
        calendar.update(parser.days())
    expected = [(start+timedelta(days=i)).isoformat() for i in range(365)]
    if any(day not in calendar for day in expected):
        raise ValueError("Incomplete public calendar; keeping existing artwork")
    days = [calendar[day] for day in expected]
    profile = fetch(f"https://api.github.com/users/{USER}", api=True)
    repos = []
    page = 1
    while True:
        batch = fetch(f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}", api=True)
        repos.extend(repo for repo in batch if not repo.get("private", False))
        if len(batch) < 100:
            break
        page += 1
    snapshot, assets = render(profile, repos, days, today)
    # Fetch and validate everything before replacing any existing asset.
    for name, svg in assets.items():
        target = ROOT/"assets"/name
        target.parent.mkdir(exist_ok=True)
        target.write_text(svg)
    (ROOT/"data").mkdir(exist_ok=True)
    (ROOT/"data"/"public-profile.json").write_text(json.dumps(snapshot, indent=2)+"\n")
    print(f"Rendered @{USER}: {snapshot['contributions']:,} contributions, {len(repos)} public repositories, {today}")


if __name__ == "__main__":
    main()
