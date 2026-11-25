# NHL Standings & Playoff Simulator

An NHL standings tracker and what-if playoff simulator built with Python, COBOL, Fortran, and a browser dashboard. It pulls live data from the public NHL API, applies official NHL standings and seeding rules in COBOL, runs strength-of-schedule and Monte Carlo simulations in Fortran, and renders an interactive HTML/JS view.

## How It Works

* **Python (`get_teams.py`, `build_html.py`):** Pulls live NHL standings, schedules, and tonight's games from `api-web.nhle.com`, writes fixed-width data files, tracks daily rank changes, and builds the HTML/JS dashboard.
* **COBOL (`sort_teams.cob`):** Sorts teams using official NHL tiebreakers (`PTS`, `GP`, `RW`, `ROW`, `W`) and assigns division and wild card playoff seeds (`A1–A3`, `M1–M3`, `C1–C3`, `P1–P3`, `WC1`, `WC2`).
* **Fortran (`power_ratings.f90`):** Computes Pythagorean strength, solves a 32x32 Colley Matrix strength-of-schedule system, and runs 100,000 Monte Carlo simulations of the rest of the regular season and best-of-seven playoffs to output Playoff %, Stanley Cup %, and GD/GP.
* **HTML/JS (`index.html`):** Displays conference, division, and playoff picture filters, first-round matchup probabilities, daily rank movement, and an interactive what-if predictor for tonight's games.

## Project Structure

```text
.
├── Makefile
├── get_teams.py
├── sort_teams.cob
├── power_ratings.f90
├── build_html.py
└── README.md

## Setup & Usage
Requires Python 3, GnuCOBOL (cobc), and gfortran.

Bash
make run

