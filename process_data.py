"""
process_data.py — clean and convert NASA / CSA mission data for "Mission Control: Moon".

Input : data/sources/*.csv   (values copied from official NASA and CSA pages; each row keeps its source_url)
Output: output/game_data.json        one file the game loads
        output/*_clean.csv           cleaned tables in metric units
        output/apollo11_timeline.png chart of the mission timeline

Run:  pip install pandas matplotlib
      python3 process_data.py
"""

import json
from pathlib import Path
import pandas as pd

SRC = Path(__file__).parent / "data" / "sources"
OUT = Path(__file__).parent / "output"
OUT.mkdir(exist_ok=True)

FT_TO_M = 0.3048
LBF_TO_KN = 0.00444822
TO_KM = {"statute_mile": 1.609344, "nautical_mile": 1.852, "km": 1.0}
MOON_RADIUS_KM = 1737.4
EARTH_RADIUS_KM = 6378.1


def load(name):
    df = pd.read_csv(SRC / name)
    df.columns = df.columns.str.strip()
    df = df.apply(lambda c: c.str.strip() if c.dtype == "object" else c)
    missing = df.drop(columns=[c for c in df.columns if c in ("notes", "burn_seconds")]).isna().sum().sum()
    if missing:
        print(f"  warning: {name} has {missing} empty cells")
    if not df["source_url"].str.startswith("https://").all():
        raise ValueError(f"{name}: every row needs an https source_url")
    return df.drop_duplicates()


def get_to_hours(t):
    h, m, s = (float(x) for x in t.split(":"))
    return h + m / 60 + s / 3600


# ---------- Saturn V stages ----------
stages = load("saturn_v_stages.csv")
stages["height_m"] = (stages.height_ft * FT_TO_M).round(1)
stages["diameter_m"] = (stages.diameter_ft * FT_TO_M).round(1)
stages["thrust_total_kN"] = (stages.thrust_total_lbf * LBF_TO_KN).round(0)
stages["thrust_each_kN"] = (stages.thrust_each_lbf * LBF_TO_KN).round(0)

# ---------- Apollo 11 timeline ----------
timeline = load("apollo11_timeline.csv")
timeline["hours"] = timeline.ground_elapsed_time.apply(get_to_hours).round(3)
timeline["day"] = (timeline.hours // 24 + 1).astype(int)
timeline = timeline.sort_values("hours").reset_index(drop=True)
assert timeline.hours.is_monotonic_increasing, "events out of order"

# ---------- orbits ----------
orbits = load("apollo11_orbits.csv")
orbits["low_km"] = (orbits.low_point * orbits.unit.map(TO_KM)).round(1)
orbits["high_km"] = (orbits.high_point * orbits.unit.map(TO_KM)).round(1)
radius = orbits.body.map({"Earth": EARTH_RADIUS_KM, "Moon": MOON_RADIUS_KM})
rp, ra = radius + orbits.low_km, radius + orbits.high_km
orbits["eccentricity"] = ((ra - rp) / (ra + rp)).round(4)   # how stretched the ellipse is

# ---------- CSA ----------
csa = load("csa_moon_contributions.csv").sort_values("year")

# ---------- save ----------
stages.to_csv(OUT / "saturn_v_stages_clean.csv", index=False)
timeline.to_csv(OUT / "apollo11_timeline_clean.csv", index=False)
orbits.to_csv(OUT / "apollo11_orbits_clean.csv", index=False)
csa.to_csv(OUT / "csa_moon_contributions_clean.csv", index=False)

game = {
    "sources": sorted(set(pd.concat([stages.source_url, timeline.source_url, orbits.source_url, csa.source_url]))),
    "saturn_v_stages": stages[["stage", "contractor", "height_m", "diameter_m", "engine_type", "engine_count",
                               "fuel", "oxidizer", "thrust_total_kN"]].to_dict("records"),
    "apollo11_timeline": timeline[["event", "hours", "day", "burn_seconds", "notes"]]
        .astype(object).where(timeline[["event", "hours", "day", "burn_seconds", "notes"]].notna(), None).to_dict("records"),
    "apollo11_orbits": orbits[["phase", "body", "low_km", "high_km", "eccentricity"]].to_dict("records"),
    "canada_on_the_moon": csa[["year", "mission", "contribution"]].to_dict("records"),
}
with open(OUT / "game_data.json", "w", encoding="utf-8") as f:
    json.dump(game, f, indent=1, ensure_ascii=False)

# ---------- summary ----------
print(f"Saturn V stages: {len(stages)}  | Apollo 11 events: {len(timeline)}  | orbits: {len(orbits)}  | CSA items: {len(csa)}")
print(f"Mission length: {timeline.hours.max():.1f} hours ({timeline.hours.max() / 24:.1f} days)")
print(f"Total burn time listed: {timeline.burn_seconds.sum():.0f} s")
print(orbits[["phase", "low_km", "high_km", "eccentricity"]].to_string(index=False))

# ---------- chart ----------
try:
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.axhline(0, lw=1, color="0.6")
    ax.scatter(timeline.hours, [0] * len(timeline), s=40, zorder=3)
    levels = [3, -3, 1.8, -1.8, 4.2, -4.2, 0.9]
    for i, r in timeline.iterrows():
        y = levels[i % len(levels)]
        ax.plot([r.hours, r.hours], [0, y], lw=0.8, color="0.7", zorder=1)
        ax.text(r.hours, y + (0.15 if y > 0 else -0.15), f"{r.event}\n{r.hours:.1f} h",
                ha="center", va="bottom" if y > 0 else "top", fontsize=7.5)
    ax.set_ylim(-5.5, 5.5)
    ax.set_xlim(-12, 210)
    ax.set_yticks([])
    ax.set_xlabel("Hours after launch")
    ax.set_title("Apollo 11 mission timeline (data: NASA)")
    for s in ("left", "right", "top"):
        ax.spines[s].set_visible(False)
    plt.tight_layout()
    plt.savefig(OUT / "apollo11_timeline.png", dpi=150)
    print("Chart saved: output/apollo11_timeline.png")
except ImportError:
    print("Install matplotlib to also get the chart.")
