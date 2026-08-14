"""Coleta o calendário público de contribuições do GitHub e grava data/contributions.json.

Usa o HTML público em https://github.com/users/<user>/contributions — não exige token.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USER = os.environ.get("GH_PROFILE_USER", "methooficial")
URL = f"https://github.com/users/{USER}/contributions"
OUT = Path(__file__).resolve().parent.parent / "data" / "contributions.json"

COUNT_RE = re.compile(r"^(?:(\d[\d,]*)|No)\s+contributions?", re.IGNORECASE)


def fetch_html(url: str) -> str:
    resp = requests.get(
        url,
        headers={
            "User-Agent": "metho-profile-art/1.0 (+https://metho.com.br)",
            "Accept": "text/html",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.text


def parse_days(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")

    # Os totais ficam em <tool-tip for="<id do td>">N contributions on ...</tool-tip>
    counts: dict[str, int] = {}
    for tip in soup.find_all("tool-tip"):
        target = tip.get("for")
        if not target:
            continue
        match = COUNT_RE.match(tip.get_text(strip=True))
        if not match:
            continue
        raw = match.group(1)
        counts[target] = int(raw.replace(",", "")) if raw else 0

    days: list[dict] = []
    for cell in soup.select("td.ContributionCalendar-day[data-date]"):
        cell_id = cell.get("id", "")
        days.append(
            {
                "date": cell["data-date"],
                "level": int(cell.get("data-level", 0)),
                "count": counts.get(cell_id, 0),
            }
        )

    days.sort(key=lambda day: day["date"])
    return days


def streaks(days: list[dict]) -> tuple[int, int]:
    """Retorna (streak atual, maior streak). Ignora dias futuros."""
    today = date.today().isoformat()
    past = [day for day in days if day["date"] <= today]

    longest = running = 0
    for day in past:
        running = running + 1 if day["count"] > 0 else 0
        longest = max(longest, running)

    current = 0
    for day in reversed(past):
        if day["count"] > 0:
            current += 1
        elif current or day["date"] != today:
            # Um dia zerado só encerra a sequência se não for o dia corrente.
            break
    return current, longest


def monthly_totals(days: list[dict]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for day in days:
        month = day["date"][:7]
        totals[month] = totals.get(month, 0) + day["count"]
    return totals


def main() -> int:
    days = parse_days(fetch_html(URL))
    if not days:
        print("nenhum dia encontrado — layout do GitHub pode ter mudado", file=sys.stderr)
        return 1

    active = [day for day in days if day["count"] > 0]
    best = max(days, key=lambda day: day["count"])
    current, longest = streaks(days)

    payload = {
        "user": USER,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "range": {"from": days[0]["date"], "to": days[-1]["date"]},
        "total": sum(day["count"] for day in days),
        "active_days": len(active),
        "best_day": {"date": best["date"], "count": best["count"]},
        "current_streak": current,
        "longest_streak": longest,
        "monthly": monthly_totals(days),
        "days": days,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(days)} dias · {payload['total']} contribuições → {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
