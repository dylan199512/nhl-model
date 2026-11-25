from datetime import datetime
import json
from pathlib import Path

# 1. Read Fortran Power Rankings, Colley Ratings, Playoff %, and Stanley Cup %
fortran_data = {}
with open("fortran_ranked.txt", "r", encoding="ascii") as f:
  for line in f:
    parts = line.split()
    abbr = parts[1]
    fortran_data[abbr] = {
        "p_rank": int(parts[0]),
        "pyth": float(parts[2]),
        "colley": float(parts[3]),
        "proj_pts": float(parts[4]),
        "diff_gp": float(parts[5]),
        "playoff_pct": float(parts[6]),
        "cup_pct": float(parts[7]),
    }

# 2. Read COBOL Standings, Playoff Seeds, and RW Tiebreakers
CONF_MAP = {"A": "E", "M": "E", "C": "W", "P": "W"}
merged_teams = []

with open("teams_sorted.txt", "r", encoding="ascii") as f:
  for idx, line in enumerate(f):
    abbr = line[0:3]
    div = line[3:4]
    gp = int(line[4:6])
    w = int(line[6:8])
    l = int(line[8:10])
    otl = int(line[10:12])
    pts = int(line[12:15])
    seed = line[15:18].strip() or "---"
    rw = int(line[18:20]) if len(line.strip()) >= 20 else w

    f_stats = fortran_data[abbr]
    cobol_rank = idx + 1

    merged_teams.append({
        "abbr": abbr,
        "div": div,
        "conf": CONF_MAP[div],
        "gp": gp,
        "w": w,
        "l": l,
        "otl": otl,
        "pts": pts,
        "rw": rw,
        "base_seed": seed,
        "base_rank": cobol_rank,
        "f_rank": f_stats["p_rank"],
        "pyth": f_stats["pyth"],
        "colley": f_stats["colley"],
        "proj_pts": f_stats["proj_pts"],
        "playoff_pct": f_stats["playoff_pct"],
        "cup_pct": f_stats["cup_pct"],
        "diff_gp": f_stats["diff_gp"],
    })

# 3. Track Daily Rank Movement in rank_history.json
today_str = datetime.now().strftime("%Y-%m-%d")
history_path = Path("rank_history.json")
current_ranks = {t["abbr"]: t["base_rank"] for t in merged_teams}

if history_path.exists():
  history = json.loads(history_path.read_text(encoding="utf-8"))
  if history.get("date") != today_str:
    prev_ranks = history.get("ranks", current_ranks)
    history_path.write_text(
        json.dumps(
            {
                "date": today_str,
                "ranks": current_ranks,
                "prev_ranks": prev_ranks,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
  else:
    prev_ranks = history.get("prev_ranks", current_ranks)
else:
  prev_ranks = current_ranks
  history_path.write_text(
      json.dumps(
          {"date": today_str, "ranks": current_ranks, "prev_ranks": prev_ranks},
          indent=2,
      ),
      encoding="utf-8",
  )

for t in merged_teams:
  t["move"] = prev_ranks.get(t["abbr"], t["base_rank"]) - t["base_rank"]

# 4. Load Tonight's Unplayed Games
tonight_path = Path("tonight_games.json")
tonight_games = (
    json.loads(tonight_path.read_text(encoding="utf-8"))
    if tonight_path.exists()
    else []
)

updated_stamp = datetime.now().strftime("%b %d, %Y at %I:%M %p")
teams_json = json.dumps(merged_teams)
games_json = json.dumps(tonight_games)

# 5. Generate Interactive HTML Dashboard
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>NHL Polyglot Analytics &amp; What-If Simulator</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #f4f4f5; color: #18181b; margin: 32px; }}
        .header {{ display: flex; justify-content: space-between; align-items: flex-end; flex-wrap: wrap; gap: 12px; margin-bottom: 18px; }}
        h2 {{ margin: 0 0 4px 0; }}
        .subtitle {{ color: #52525b; margin: 0; font-size: 0.95rem; }}
        .timestamp {{ background: #e4e4e7; color: #3f3f46; padding: 6px 12px; border-radius: 6px; font-size: 0.82rem; font-weight: 600; }}

        /* Tonight's Games Predictor Panel */
        .tonight-panel {{ background: white; padding: 16px 18px; border-radius: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.06); margin-bottom: 20px; border-left: 4px solid #2563eb; }}
        .tonight-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px; }}
        .tonight-header h3 {{ margin: 0; font-size: 0.95rem; text-transform: uppercase; letter-spacing: 0.04em; color: #18181b; }}
        .tonight-sub {{ font-size: 0.84rem; color: #52525b; }}
        .reset-btn {{ padding: 5px 12px; border: 1px solid #d4d4d8; background: #fafafa; border-radius: 6px; cursor: pointer; font-size: 0.8rem; font-weight: 600; }}
        .reset-btn:hover {{ background: #e4e4e7; }}
        .reset-btn:disabled {{ opacity: 0.45; cursor: default; }}
        .games-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(235px, 1fr)); gap: 10px; }}
        .game-pill {{ border: 1px solid #e4e4e7; border-radius: 8px; padding: 8px 10px; background: #fafafa; }}
        .game-time {{ font-size: 0.72rem; color: #71717a; font-weight: 600; margin-bottom: 6px; display: flex; justify-content: space-between; }}
        .pick-row {{ display: flex; gap: 5px; align-items: center; }}
        .pick-btn {{
            flex: 1; padding: 6px 4px; border: 1px solid #d4d4d8; background: white;
            border-radius: 5px; cursor: pointer; font-weight: 700; font-size: 0.82rem; transition: all 0.12s;
        }}
        .pick-btn:hover {{ border-color: #18181b; }}
        .pick-btn.selected {{ background: #18181b; color: white; border-color: #18181b; }}
        .ot-btn {{
            padding: 6px 7px; border: 1px solid #d4d4d8; background: white; color: #71717a;
            border-radius: 5px; cursor: pointer; font-weight: 700; font-size: 0.72rem;
        }}
        .ot-btn.active {{ background: #fef3c7; color: #92400e; border-color: #f59e0b; }}

        /* Playoff Bracket Cards */
        .bracket-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 18px; margin-bottom: 24px; }}
        .conf-col {{ background: white; padding: 16px 18px; border-radius: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.06); }}
        .conf-col h3 {{ margin: 0 0 12px 0; font-size: 0.95rem; text-transform: uppercase; letter-spacing: 0.04em; color: #3f3f46; }}
        .series-card {{ border: 1px solid #e4e4e7; border-radius: 8px; padding: 9px 12px; margin-bottom: 9px; background: #fafafa; }}
        .series-card:last-child {{ margin-bottom: 0; }}
        .series-row {{ display: flex; justify-content: space-between; align-items: center; font-size: 0.9rem; }}
        .series-row small {{ color: #71717a; }}
        .seed-pill {{ display: inline-block; width: 34px; text-align: center; background: #18181b; color: white; border-radius: 4px; font-size: 0.72rem; font-weight: 700; padding: 2px 0; margin-right: 6px; }}
        .seed-pill.shifted {{ background: #2563eb; }}
        .series-odds {{ font-weight: 700; font-variant-numeric: tabular-nums; }}
        .prob-bar {{ height: 5px; background: #e4e4e7; border-radius: 999px; overflow: hidden; margin: 5px 0; }}
        .prob-fill {{ height: 100%; background: #2563eb; }}

        /* Filters & Table */
        .filters {{ margin: 14px 0; display: flex; gap: 8px; flex-wrap: wrap; }}
        .filters button {{
            padding: 7px 14px; border: 1px solid #d4d4d8; background: white;
            border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.85rem;
        }}
        .filters button:hover {{ background: #e4e4e7; }}
        .filters button.active {{ background: #18181b; color: white; border-color: #18181b; }}

        table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.08); font-size: 0.9rem; }}
        th, td {{ padding: 10px 10px; text-align: center; border-bottom: 1px solid #e4e4e7; font-variant-numeric: tabular-nums; }}
        th {{
            background: #18181b; color: white; font-weight: 600; text-transform: uppercase;
            font-size: 0.74rem; cursor: pointer; user-select: none;
        }}
        th:hover {{ background: #27272a; }}
        tr:hover td {{ background: #fafafa; }}
        tr.row-shifted td {{ background: #eff6ff; }}
        .positive {{ color: #16a34a; font-weight: 700; }}
        .negative {{ color: #dc2626; font-weight: 700; }}
        .neutral {{ color: #a1a1aa; }}
        .move-badge {{ font-size: 0.74rem; margin-left: 4px; }}
        .shift-note {{ display: block; font-size: 0.68rem; color: #2563eb; font-weight: 700; }}
        .left-align {{ text-align: left; }}
        .badge-div {{ background: #dbeafe; color: #1e40af; padding: 3px 8px; border-radius: 999px; font-size: 0.74rem; font-weight: 700; }}
        .badge-wc  {{ background: #fef3c7; color: #92400e; padding: 3px 8px; border-radius: 999px; font-size: 0.74rem; font-weight: 700; }}
        .badge-out {{ color: #a1a1aa; font-size: 0.85rem; }}
        .odds-high {{ color: #16a34a; font-weight: 700; }}
        .odds-mid  {{ color: #d97706; font-weight: 700; }}
        .odds-low  {{ color: #71717a; }}
        .cup-elite {{ color: #1d4ed8; font-weight: 700; }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h2>NHL Official Standings &amp; What-If Playoff Simulator</h2>
            <p class="subtitle">Official standings, tiebreakers &amp; seeding in <strong>COBOL</strong> &middot; Colley Matrix, Pythagorean strength &amp; 100,000 Monte Carlo seasons in <strong>Fortran</strong></p>
        </div>
        <div class="timestamp">Last Updated: {updated_stamp}</div>
    </div>

    <div class="tonight-panel">
        <div class="tonight-header">
            <div>
                <h3>Tonight's Games &mdash; Interactive What-If Predictor</h3>
                <span class="tonight-sub" id="whatif-status">Click any winner below to preview live playoff seed changes (toggle <strong>OT</strong> to award the loser 1 point).</span>
            </div>
            <button class="reset-btn" id="reset-btn" onclick="resetPicks()" disabled>Reset Picks</button>
        </div>
        <div class="games-grid" id="tonight-grid"></div>
    </div>

    <div class="bracket-grid" id="bracket-grid"></div>

    <div class="filters">
        <button class="active" onclick="setFilter('ALL', this)">All (32)</button>
        <button onclick="setFilter('PLAYOFFS', this)">Playoff Picture (16)</button>
        <button onclick="setFilter('CONF:E', this)">Eastern Conf</button>
        <button onclick="setFilter('CONF:W', this)">Western Conf</button>
        <button onclick="setFilter('DIV:A', this)">Atlantic (A)</button>
        <button onclick="setFilter('DIV:M', this)">Metropolitan (M)</button>
        <button onclick="setFilter('DIV:C', this)">Central (C)</button>
        <button onclick="setFilter('DIV:P', this)">Pacific (P)</button>
    </div>

    <table id="nhl-table">
        <thead>
            <tr>
                <th data-col="c_rank" data-type="num">Official ▲</th>
                <th data-col="seed" data-type="str">Seed</th>
                <th data-col="f_rank" data-type="num">Power</th>
                <th data-col="delta" data-type="num">Diff</th>
                <th data-col="abbr" data-type="str" class="left-align">Team</th>
                <th data-col="div" data-type="str">Div</th>
                <th data-col="gp" data-type="num">GP</th>
                <th data-col="record" data-type="str">Record</th>
                <th data-col="pts" data-type="num">Pts</th>
                <th data-col="rw" data-type="num">RW</th>
                <th data-col="pyth" data-type="num">Pyth %</th>
                <th data-col="colley" data-type="num">Colley</th>
                <th data-col="proj_pts" data-type="num">Proj. Pts</th>
                <th data-col="playoff_pct" data-type="num">Playoff %</th>
                <th data-col="cup_pct" data-type="num">Cup %</th>
                <th data-col="diff_gp" data-type="num">GD / GP</th>
            </tr>
        </thead>
        <tbody id="table-body"></tbody>
    </table>

    <script>
        const BASE_TEAMS = {teams_json};
        const TONIGHT_GAMES = {games_json};

        // picks[gameId] = {{ winner: 'AWAY' | 'HOME' | null, ot: boolean }}
        const picks = {{}};
        TONIGHT_GAMES.forEach(g => {{ picks[g.id] = {{ winner: null, ot: false }}; }});

        let filterMode = 'ALL';
        let sortCol = 'c_rank';
        let sortAsc = true;

        function blendedStrength(t) {{
            return 0.5 * t.pyth + 0.5 * t.colley;
        }}

        function homeWinChance(awayAbbr, homeAbbr) {{
            const tMap = Object.fromEntries(BASE_TEAMS.map(t => [t.abbr, t]));
            const ph = blendedStrength(tMap[homeAbbr]);
            const pa = blendedStrength(tMap[awayAbbr]);
            const log5 = (ph * (1 - pa)) / (ph * (1 - pa) + (1 - ph) * pa);
            return Math.min(0.92, Math.max(0.08, log5 + 0.035));
        }}

        function renderTonightGames() {{
            const grid = document.getElementById('tonight-grid');
            if (!TONIGHT_GAMES.length) {{
                grid.innerHTML = '<div class="tonight-sub">No remaining games scheduled for today.</div>';
                return;
            }}

            grid.innerHTML = TONIGHT_GAMES.map(g => {{
                const state = picks[g.id];
                const timeLabel = g.start_utc
                    ? new Date(g.start_utc).toLocaleTimeString([], {{ hour: 'numeric', minute: '2-digit' }})
                    : 'Tonight';
                const homePct = Math.round(homeWinChance(g.away, g.home) * 100);
                const awayPct = 100 - homePct;

                return `
                <div class="game-pill">
                    <div class="game-time">
                        <span>${{timeLabel}}</span>
                        <span>${{g.away}} ${{awayPct}}% &middot; ${{g.home}} ${{homePct}}%</span>
                    </div>
                    <div class="pick-row">
                        <button class="pick-btn ${{state.winner === 'AWAY' ? 'selected' : ''}}"
                                onclick="toggleWinner(${{g.id}}, 'AWAY')">@ ${{g.away}}</button>
                        <button class="ot-btn ${{state.ot ? 'active' : ''}}"
                                title="Toggle Overtime / Shootout (+1 pt to loser)"
                                onclick="toggleOT(${{g.id}})">OT</button>
                        <button class="pick-btn ${{state.winner === 'HOME' ? 'selected' : ''}}"
                                onclick="toggleWinner(${{g.id}}, 'HOME')">${{g.home}}</button>
                    </div>
                </div>`;
            }}).join('');
        }}

        function toggleWinner(gameId, side) {{
            picks[gameId].winner = (picks[gameId].winner === side) ? null : side;
            updateDashboard();
        }}

        function toggleOT(gameId) {{
            picks[gameId].ot = !picks[gameId].ot;
            if (picks[gameId].winner) updateDashboard();
            else renderTonightGames();
        }}

        function resetPicks() {{
            TONIGHT_GAMES.forEach(g => {{ picks[g.id] = {{ winner: null, ot: false }}; }});
            updateDashboard();
        }}

        function computeSimulatedStandings() {{
            const teams = BASE_TEAMS.map(t => ({{ ...t }}));
            const byAbbr = Object.fromEntries(teams.map(t => [t.abbr, t]));
            let activeCount = 0;

            TONIGHT_GAMES.forEach(g => {{
                const p = picks[g.id];
                if (!p.winner) return;
                activeCount++;

                const winTeam  = (p.winner === 'HOME') ? byAbbr[g.home] : byAbbr[g.away];
                const loseTeam = (p.winner === 'HOME') ? byAbbr[g.away] : byAbbr[g.home];

                winTeam.gp += 1;
                winTeam.w  += 1;
                winTeam.pts += 2;
                if (!p.ot) winTeam.rw += 1;

                loseTeam.gp += 1;
                if (p.ot) {{
                    loseTeam.otl += 1;
                    loseTeam.pts += 1;
                }} else {{
                    loseTeam.l += 1;
                }}
            }});

            // Sort using NHL official tiebreakers: PTS -> GP (asc) -> RW -> W -> GD/GP
            teams.sort((a, b) =>
                (b.pts - a.pts) ||
                (a.gp - b.gp) ||
                (b.rw - a.rw) ||
                (b.w - a.w) ||
                (b.diff_gp - a.diff_gp)
            );

            // Re-assign Division Top 3 and Conference Wild Card seeds (matching COBOL)
            const divCounts = {{ A: 0, M: 0, C: 0, P: 0 }};
            const wcCounts  = {{ E: 0, W: 0 }};
            const seedMap   = {{}};

            teams.forEach((t, idx) => {{
                t.c_rank = idx + 1;
                t.delta  = t.c_rank - t.f_rank;
                t.record = `${{t.w}}-${{t.l}}-${{t.otl}}`;
                t.seed   = '---';

                if (divCounts[t.div] < 3) {{
                    divCounts[t.div] += 1;
                    t.seed = `${{t.div}}${{divCounts[t.div]}}`;
                    seedMap[t.seed] = t;
                }} else if (wcCounts[t.conf] < 2) {{
                    wcCounts[t.conf] += 1;
                    t.seed = `WC${{wcCounts[t.conf]}}`;
                    seedMap[`${{t.conf}}-${{t.seed}}`] = t;
                }}
                t.in_playoffs = (t.seed !== '---') ? '1' : '0';
                t.seed_changed = (t.seed !== t.base_seed);
            }});

            return {{ teams, seedMap, activeCount }};
        }}

        function seriesWinProb(hi, lo) {{
            const ph = blendedStrength(hi);
            const pl = blendedStrength(lo);
            const baseP = (ph * (1 - pl)) / (ph * (1 - pl) + (1 - ph) * pl);
            const homeGames = new Set([1, 2, 5, 7]);

            let dp = new Map([['0,0', 1.0]]);
            let hiProb = 0.0;

            for (let game = 1; game <= 7; game++) {{
                const nextDp = new Map();
                const pGame = Math.min(0.92, Math.max(0.08, baseP + (homeGames.has(game) ? 0.035 : -0.035)));
                for (const [key, prob] of dp.entries()) {{
                    const [hw, lw] = key.split(',').map(Number);
                    if (hw === 4 || lw === 4) continue;
                    if (hw + 1 === 4) hiProb += prob * pGame;
                    else nextDp.set(`${{hw + 1}},${{lw}}`, (nextDp.get(`${{hw + 1}},${{lw}}`) || 0) + prob * pGame);
                    if (lw + 1 < 4) nextDp.set(`${{hw}},${{lw + 1}}`, (nextDp.get(`${{hw}},${{lw + 1}}`) || 0) + prob * (1 - pGame));
                }}
                dp = nextDp;
            }}
            return hiProb * 100;
        }}

        function renderBracket(seedMap) {{
            function confColumn(div1, div2, confCode, label) {{
                const w1 = seedMap[`${{div1}}1`];
                const w2 = seedMap[`${{div2}}1`];
                const wc1 = seedMap[`${{confCode}}-WC1`];
                const wc2 = seedMap[`${{confCode}}-WC2`];

                const pairs = (w1.c_rank < w2.c_rank)
                    ? [
                        [`${{div1}}1`, w1, 'WC2', wc2],
                        [`${{div1}}2`, seedMap[`${{div1}}2`], `${{div1}}3`, seedMap[`${{div1}}3`]],
                        [`${{div2}}1`, w2, 'WC1', wc1],
                        [`${{div2}}2`, seedMap[`${{div2}}2`], `${{div2}}3`, seedMap[`${{div2}}3`]]
                      ]
                    : [
                        [`${{div2}}1`, w2, 'WC2', wc2],
                        [`${{div2}}2`, seedMap[`${{div2}}2`], `${{div2}}3`, seedMap[`${{div2}}3`]],
                        [`${{div1}}1`, w1, 'WC1', wc1],
                        [`${{div1}}2`, seedMap[`${{div1}}2`], `${{div1}}3`, seedMap[`${{div1}}3`]]
                      ];

                const cards = pairs.map(([hiSeed, hi, loSeed, lo]) => {{
                    const hiProb = seriesWinProb(hi, lo);
                    const loProb = 100 - hiProb;
                    return `
                    <div class="series-card">
                        <div class="series-row">
                            <span><span class="seed-pill ${{hi.seed_changed ? 'shifted' : ''}}">${{hiSeed}}</span> <strong>${{hi.abbr}}</strong> <small>(${{hi.pts}} pts)</small></span>
                            <span class="series-odds">${{hiProb.toFixed(1)}}%</span>
                        </div>
                        <div class="prob-bar"><div class="prob-fill" style="width: ${{hiProb.toFixed(1)}}%;"></div></div>
                        <div class="series-row">
                            <span><span class="seed-pill ${{lo.seed_changed ? 'shifted' : ''}}">${{loSeed}}</span> <strong>${{lo.abbr}}</strong> <small>(${{lo.pts}} pts)</small></span>
                            <span class="series-odds">${{loProb.toFixed(1)}}%</span>
                        </div>
                    </div>`;
                }}).join('');

                return `<div class="conf-col"><h3>${{label}}</h3>${{cards}}</div>`;
            }}

            document.getElementById('bracket-grid').innerHTML =
                confColumn('A', 'M', 'E', 'Eastern Conference &mdash; Round 1') +
                confColumn('C', 'P', 'W', 'Western Conference &mdash; Round 1');
        }}

        function renderTable(teams) {{
            const filtered = teams.filter(t => {{
                if (filterMode === 'ALL') return true;
                if (filterMode === 'PLAYOFFS') return t.in_playoffs === '1';
                if (filterMode.startsWith('CONF:')) return t.conf === filterMode.split(':')[1];
                if (filterMode.startsWith('DIV:')) return t.div === filterMode.split(':')[1];
                return true;
            }});

            const strCols = new Set(['seed', 'abbr', 'div', 'record']);
            filtered.sort((a, b) => {{
                if (strCols.has(sortCol)) {{
                    return sortAsc
                        ? String(a[sortCol]).localeCompare(String(b[sortCol]))
                        : String(b[sortCol]).localeCompare(String(a[sortCol]));
                }}
                return sortAsc ? (a[sortCol] - b[sortCol]) : (b[sortCol] - a[sortCol]);
            }});

            document.getElementById('table-body').innerHTML = filtered.map(t => {{
                const deltaStr = t.delta > 0 ? `+${{t.delta}}` : (t.delta < 0 ? `${{t.delta}}` : '--');
                const deltaClass = t.delta > 0 ? 'positive' : (t.delta < 0 ? 'negative' : 'neutral');

                let moveHtml = '';
                if (t.move > 0) moveHtml = `<span class="move-badge positive">▲${{t.move}}</span>`;
                else if (t.move < 0) moveHtml = `<span class="move-badge negative">▼${{Math.abs(t.move)}}</span>`;

                let seedHtml = `<span class="badge-out">---</span>`;
                if (t.seed.startsWith('WC')) seedHtml = `<span class="badge-wc">${{t.seed}}</span>`;
                else if (t.seed !== '---') seedHtml = `<span class="badge-div">${{t.seed}}</span>`;

                if (t.seed_changed) {{
                    seedHtml += `<span class="shift-note">was ${{t.base_seed}}</span>`;
                }}

                const pStr = (t.playoff_pct > 0 && t.playoff_pct < 0.1) ? '&lt;0.1%' : `${{t.playoff_pct.toFixed(1)}}%`;
                const pClass = t.playoff_pct >= 75 ? 'odds-high' : (t.playoff_pct >= 25 ? 'odds-mid' : 'odds-low');
                const cStr = (t.cup_pct > 0 && t.cup_pct < 0.1) ? '&lt;0.1%' : `${{t.cup_pct.toFixed(1)}}%`;
                const cClass = t.cup_pct >= 8.0 ? 'cup-elite' : '';
                const gdStr = (t.diff_gp >= 0 ? '+' : '') + t.diff_gp.toFixed(2);

                return `
                <tr class="${{t.seed_changed ? 'row-shifted' : ''}}">
                    <td><strong>${{t.c_rank}}</strong>${{moveHtml}}</td>
                    <td>${{seedHtml}}</td>
                    <td><strong>${{t.f_rank}}</strong></td>
                    <td class="${{deltaClass}}">${{deltaStr}}</td>
                    <td class="left-align"><strong>${{t.abbr}}</strong></td>
                    <td>${{t.div}}</td>
                    <td>${{t.gp}}</td>
                    <td>${{t.record}}</td>
                    <td><strong>${{t.pts}}</strong></td>
                    <td>${{t.rw}}</td>
                    <td>${{t.pyth.toFixed(4)}}</td>
                    <td>${{t.colley.toFixed(4)}}</td>
                    <td>${{t.proj_pts.toFixed(1)}}</td>
                    <td class="${{pClass}}">${{pStr}}</td>
                    <td class="${{cClass}}">${{cStr}}</td>
                    <td>${{gdStr}}</td>
                </tr>`;
            }}).join('');
        }}

        function updateDashboard() {{
            renderTonightGames();
            const {{ teams, seedMap, activeCount }} = computeSimulatedStandings();
            renderBracket(seedMap);
            renderTable(teams);

            const resetBtn = document.getElementById('reset-btn');
            const statusEl = document.getElementById('whatif-status');
            resetBtn.disabled = (activeCount === 0);
            statusEl.innerHTML = activeCount > 0
                ? `Simulating <strong>${{activeCount}}</strong> result${{activeCount > 1 ? 's' : ''}} from tonight's slate &mdash; changed playoff seeds are highlighted in blue.`
                : `Click any winner below to preview live playoff seed changes (toggle <strong>OT</strong> to award the loser 1 point).`;
        }}

        function setFilter(mode, btn) {{
            filterMode = mode;
            document.querySelectorAll('.filters button').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            updateDashboard();
        }}

        document.querySelectorAll('#nhl-table th').forEach(th => {{
            th.addEventListener('click', () => {{
                const col = th.dataset.col;
                const type = th.dataset.type;
                if (sortCol === col) {{
                    sortAsc = !sortAsc;
                }} else {{
                    sortCol = col;
                    sortAsc = (col === 'c_rank' || col === 'f_rank' || type === 'str');
                }}
                document.querySelectorAll('#nhl-table th').forEach(h => {{
                    h.textContent = h.textContent.replace(/ [▲▼]$/, '');
                }});
                th.textContent += sortAsc ? ' ▲' : ' ▼';
                updateDashboard();
            }});
        }});

        updateDashboard();
    </script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
  f.write(html_content)

print("Dashboard built with Tonight's Games What-If Predictor!")