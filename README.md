# Mission Control: Moon — NASA & CSA data

Real mission data used by the game, collected from official NASA and Canadian Space Agency (CSA) sources, then cleaned and converted with Python (pandas).

## Folder layout

```
data/sources/      values taken from official pages (every row keeps its source_url)
process_data.py    cleans, validates and converts the data
output/            cleaned CSVs (metric units), game_data.json, timeline chart
moon_data.py       optional: fetches Moon positions live from the NASA JPL Horizons API
```

## Datasets

| File | What it holds | Source |
|---|---|---|
| `saturn_v_stages.csv` | All 3 stages + Instrument Unit: size, engines, thrust, fueled/dry weight, oxidizer and fuel weight | NASA SP-4029 Key Facts; NASA Apollo 11 Press Kit |
| `apollo11_timeline.csv` | 14 mission events with elapsed time and burn lengths | NASA Apollo 11 Mission Overview |
| `apollo11_orbits.csv` | Earth and lunar orbit low/high points for each phase | NASA Apollo 11 Mission Overview; Apollo 11 Lunar Surface Journal |
| `csa_moon_contributions.csv` | Canada's role in Moon exploration, 1959 to today | CSA "A quick history of Canada on the Moon"; CSA news release (Aug 2026) |

## Processing steps (`process_data.py`)

1. Load each CSV, trim spaces, drop duplicates.
2. Validate: flag empty cells, require an `https` source link on every row, check events are in time order.
3. Convert units: feet → metres, pound-force → kilonewtons, statute/nautical miles → km, mission clock (HHH:MM:SS) → hours.
4. Derive values: weights in tonnes, how much of each stage is propellant (%), oxidizer-to-fuel ratio, mission day of each event, and each orbit's eccentricity from its low and high points
   (radius = body radius + altitude; e = (r_high − r_low) / (r_high + r_low)).
5. Export cleaned CSVs, one `game_data.json` for the game, and a timeline chart.

## Run it

```
pip install pandas matplotlib
python3 process_data.py
```

## Sources

- NASA SP-4029, Apollo 11 Launch Vehicle/Spacecraft Key Facts: https://www.nasa.gov/wp-content/uploads/static/history/SP-4029/Apollo_18-11_Launch_Vehicle-Spacecraft_Key_Facts.htm
- NASA, Apollo 11 Press Kit (1969): https://www.nasa.gov/wp-content/uploads/static/apollo50th/pdf/A11_PressKit.pdf
- NASA, Apollo 11 Mission Overview: https://www.nasa.gov/missions/apollo/apollo-11-mission-overview/
- NASA, Apollo 11 Lunar Surface Journal (landing): https://www.nasa.gov/history/alsj/a11/a11.landing.html
- NASA JPL Horizons API (Moon positions): https://ssd.jpl.nasa.gov/api/horizons.api
- CSA, A quick history of Canada on the Moon: https://www.asc-csa.gc.ca/eng/youth-educators/quick-history-canada-on-the-moon.asp
- CSA, Canadarm3 news release (Aug 6, 2026): https://www.canada.ca/en/space-agency/news/2026/08/canada-intends-to-repurpose-canadarm3-investments-to-support-the-next-phase-of-lunar-exploration.html

## Tools

Python, pandas, matplotlib. Claude (AI assistant) was used to help write and test the processing code; data sources were chosen and checked against the official pages by the team.
