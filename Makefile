export PATH := /opt/homebrew/bin:/usr/local/bin:$(PATH)

.PHONY: all compile update run clean

all: compile run

compile:
	cobc -x -free sort_teams.cob -o sort_teams
	gfortran -O2 power_ratings.f90 -o power_ratings

update:
	python3 get_teams.py
	./sort_teams
	./power_ratings
	python3 build_html.py

run: update
	open index.html

clean:
	rm -f sort_teams power_ratings teams_in.txt teams_sorted.txt fortran_in.txt fortran_completed.txt fortran_sched.txt fortran_ranked.txt sortwork.tmp sort_temp.tmp index.html