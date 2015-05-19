# Swiss-system Tournament Planner
The Swiss-system Tournament Planner is a Python module that tracks players and matches in game tournaments. The program uses the [Swiss-system](https://en.wikipedia.org/wiki/Swiss-system_tournament) for pairing players in each round in a tournament -- it is a tournament which uses a non-elimination format. There are multiple rounds of competition and everyone in the tournament plays the same number of matches. The module supports multiple simultaneous tournaments and players can enter multiple tournaments. The module returns players' ranking/standing based on wins. In the event that multiple players have the same number of wins, ranking is calculated by the Opponent Match Wins (OMW).

## Setup
A quick way to setup Swiss-system Tournament Planner on your machine:

1. [Download](https://github.com/Ogodei/Swiss-Tournament-Planner/archive/master.zip) latest release from GitHub.
2. Extract zipped files to working directory.
3. Import the database (tournament.sql) onto your machine.

## Quick start
* Add players into database with the `registerPlayer(name)` function. The function takes a string as a parameter.
* Report and archive match results with by with the `reportMatch(winner_id, loser_id, tournament_id)` function. Insert the id's of the winner and loser of a match respectively
* The `swissPairings(tournament_id)` function will calculate the next pair of player matchups that satisfies the Swiss-system property.
* Finally, `playerStandings(tournament_id)` returns the current rankings/standings of the given tournament.

## What's included
In the Tournament Planner directory, you'll find the following files:
```
Swiss Tournament Planner/
    ├──tournament.py
    ├──tournament.sql
    ├──tournament_test.sql
    └──README.md
```

## Requirements
* PostgreSQL
* Python 2.7
* psycopg2 module