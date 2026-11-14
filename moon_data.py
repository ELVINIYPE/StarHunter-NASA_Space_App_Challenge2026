"""
moon_data.py — get Moon data live from NASA JPL Horizons and clean it for the game.

Source: NASA JPL Horizons API  https://ssd.jpl.nasa.gov/api/horizons.api
        (no raw file is saved; the data is downloaded straight into memory)
Output: moon_positions.csv          every row, cleaned
        moon_positions.json         daily positions for the game (small file)
        moon_perigee_apogee.csv     every closest / farthest point found
        moon_distance.png           chart of Earth-Moon distance

Run:  pip install pandas matplotlib
      python3 moon_data.py
"""

import json
import urllib.parse
import urllib.request
import numpy as np
import pandas as pd

START, STOP, STEP = "2026-11-01", "2027-12-31", "1 h"

# ---------- 1. ask NASA JPL Horizons for the Moon's position ----------
params = {
    "format": "json",
    "COMMAND": "'301'",          # 301 = the Moon
    "CENTER": "'500@399'",       # measured from Earth's center
    "EPHEM_TYPE": "'VECTORS'",   # x, y, z position and velocity
    "VEC_TABLE": "'2'",
    "OUT_UNITS": "'KM-S'",       # km and km/s
    "CSV_FORMAT": "'YES'",
    "OBJ_DATA": "'NO'",
    "MAKE_EPHEM": "'YES'",
    "START_TIME": f"'{START}'",
    "STOP_TIME": f"'{STOP}'",
    "STEP_SIZE": f"'{STEP}'",
}
url = "https://ssd.jpl.nasa.gov/api/horizons.api?" + urllib.parse.urlencode(params)
print("Downloading from NASA JPL Horizons...")
with urllib.request.urlopen(url, timeout=120) as resp:
    reply = json.load(resp)
if "error" in reply:
    raise SystemExit("Horizons error: " + reply["error"])
lines = reply["result"].splitlines()

start = lines.index("$$SOE") + 1
end = lines.index("$$EOE")
rows = [[cell.strip() for cell in line.split(",") if cell.strip()] for line in lines[start:end]]

# Vector table in CSV format: JDTDB, Calendar Date, X, Y, Z, VX, VY, VZ (+ LT, RG, RR if chosen)
names = ["jd_tdb", "date", "x_km", "y_km", "z_km", "vx_km_s", "vy_km_s", "vz_km_s", "lt_s", "range_km", "range_rate_km_s"]
df = pd.DataFrame(rows, columns=names[: len(rows[0])])

# ---------- 2. clean ----------
df["date"] = pd.to_datetime(df["date"].str.replace("A.D. ", "", regex=False), format="%Y-%b-%d %H:%M:%S.%f")
for col in df.columns:
    if col != "date":
        df[col] = pd.to_numeric(df[col], errors="coerce")
df = df.dropna().drop_duplicates(subset="date").sort_values("date").reset_index(drop=True)

# ---------- 3. add useful columns ----------
df["distance_km"] = np.sqrt(df.x_km**2 + df.y_km**2 + df.z_km**2)
df["speed_km_s"] = np.sqrt(df.vx_km_s**2 + df.vy_km_s**2 + df.vz_km_s**2)

# ---------- 4. find perigee (closest) and apogee (farthest) ----------
d = df["distance_km"]
is_perigee = (d < d.shift(1)) & (d < d.shift(-1))
is_apogee = (d > d.shift(1)) & (d > d.shift(-1))
events = pd.concat([
    df[is_perigee].assign(event="perigee"),
    df[is_apogee].assign(event="apogee"),
]).sort_values("date")[["date", "event", "distance_km", "speed_km_s"]]

# ---------- 5. save ----------
df.to_csv("moon_positions.csv", index=False)
events.to_csv("moon_perigee_apogee.csv", index=False)

daily = df.set_index("date").resample("1D").first().dropna().reset_index()
game = [
    {
        "date": r.date.strftime("%Y-%m-%d"),
        "x_km": round(r.x_km), "y_km": round(r.y_km), "z_km": round(r.z_km),
        "distance_km": round(r.distance_km), "speed_km_s": round(r.speed_km_s, 3),
    }
    for r in daily.itertuples()
]
with open("moon_positions.json", "w") as f:
    json.dump({"source": "NASA JPL Horizons, Moon (301) relative to Earth center (500@399)",
               "positions": game}, f, indent=1)

# ---------- 6. quick summary + chart ----------
print(f"Rows cleaned: {len(df)}  ({df.date.min():%Y-%m-%d} to {df.date.max():%Y-%m-%d})")
print(f"Closest distance : {d.min():,.0f} km")
print(f"Farthest distance: {d.max():,.0f} km")
print(f"Perigees found: {is_perigee.sum()}, apogees found: {is_apogee.sum()}")

try:
    import matplotlib.pyplot as plt
    plt.figure(figsize=(10, 4))
    plt.plot(df.date, df.distance_km / 1000, lw=1)
    plt.scatter(events.date, events.distance_km / 1000, c=events.event.map({"perigee": "tab:blue", "apogee": "tab:red"}), s=12)
    plt.ylabel("Earth–Moon distance (thousand km)")
    plt.title("Moon distance from Earth (data: NASA JPL Horizons)")
    plt.tight_layout()
    plt.savefig("moon_distance.png", dpi=150)
    print("Chart saved: moon_distance.png")
except ImportError:
    print("Install matplotlib to also get the chart.")