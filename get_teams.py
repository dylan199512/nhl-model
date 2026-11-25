from datetime import datetime
import json
import urllib.request

DIV_MAP = {"A": 1, "M": 2, "C": 3, "P": 4}


def fetch_json(url):
  req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
  with urllib.request.urlopen(req, timeout=15) as response:
    return json.loads(response.read().decode("utf-8"))


# 1. Grab live standings
data = fetch_json("https://api-web.nhle.com/v1/standings/now")
teams = sorted(data["standings"], key=lambda t: t["teamAbbrev"]["default"])
abbr_to_id = {
    t["teamAbbrev"]["default"]: idx for idx, t in enumerate(teams, start=1)
}

# 2. Write 19-char fixed-width file for COBOL (includes RW and ROW tiebreakers)
with open("teams_in.txt", "w", encoding="ascii") as f_cobol:
  for team in teams:
    abbr = team["teamAbbrev"]["default"]
    div = team["divisionAbbrev"]
    gp = team["gamesPlayed"]
    wins = team["wins"]
    losses = team["losses"]
    otl = team["otLosses"]
    pts = team["points"]
    rw = team["regulationWins"]
    row = team["regulationPlusOtWins"]
    f_cobol.write(
        f"{abbr:<3}{div:<1}{gp:02d}{wins:02d}{losses:02d}{otl:02d}{pts:03d}{rw:02d}{row:02d}\n"
    )

# 3. Write team stats + division ID (1-4) for Fortran
with open("fortran_in.txt", "w", encoding="ascii") as f_fort:
  for team in teams:
    abbr = team["teamAbbrev"]["default"]
    div_id = DIV_MAP[team["divisionAbbrev"]]
    gp = team["gamesPlayed"]
    wins = team["wins"]
    losses = team["losses"]
    otl = team["otLosses"]
    pts = team["points"]
    gf = team["goalFor"]
    ga = team["goalAgainst"]
    f_fort.write(
        f"{abbr} {div_id} {gp} {wins} {losses} {otl} {pts} {gf} {ga}\n"
    )

# 4. Fetch completed games, remaining games, and tonight's unplayed slate
print("Fetching NHL schedules and tonight's games...")
today_str = datetime.now().strftime("%Y-%m-%d")
completed_games = {}
remaining_games = {}
tonight_games = {}

for abbr in abbr_to_id:
  sched = fetch_json(
      f"https://api-web.nhle.com/v1/club-schedule-season/{abbr}/now"
  )
  for g in sched.get("games", []):
    if g.get("gameType") != 2:
      continue
    gid = g["id"]
    home_abbr = g["homeTeam"]["abbrev"]
    away_abbr = g["awayTeam"]["abbrev"]
    home_id = abbr_to_id[home_abbr]
    away_id = abbr_to_id[away_abbr]

    if g.get("gameState") in ("FINAL", "OFF"):
      if gid not in completed_games:
        hs = int(g["homeTeam"].get("score", 0))
        as_ = int(g["awayTeam"].get("score", 0))
        completed_games[gid] = (home_id, away_id, hs, as_)
    else:
      if gid not in remaining_games:
        remaining_games[gid] = (home_id, away_id)
      if g.get("gameDate") == today_str and gid not in tonight_games:
        tonight_games[gid] = {
            "id": gid,
            "start_utc": g.get("startTimeUTC", ""),
            "away": away_abbr,
            "home": home_abbr,
        }

with open("fortran_completed.txt", "w", encoding="ascii") as f_comp:
  f_comp.write(f"{len(completed_games)}\n")
  for home_id, away_id, hs, as_ in completed_games.values():
    f_comp.write(f"{home_id} {away_id} {hs} {as_}\n")

with open("fortran_sched.txt", "w", encoding="ascii") as f_sched:
  f_sched.write(f"{len(remaining_games)}\n")
  for home_id, away_id in remaining_games.values():
    f_sched.write(f"{home_id} {away_id}\n")

tonight_sorted = sorted(tonight_games.values(), key=lambda x: x["start_utc"])
with open("tonight_games.json", "w", encoding="utf-8") as f_tonight:
  json.dump(tonight_sorted, f_tonight, indent=2)

print(
    f"Saved {len(completed_games)} completed, {len(remaining_games)} remaining,"
    f" and {len(tonight_sorted)} games for tonight ({today_str})!"
)