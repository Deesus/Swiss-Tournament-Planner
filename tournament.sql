/******************************************
* tournament.py	-- table definitions for the tournament.
*
* Author: Dee Reddy
*
* Quick Start:
*	- connect to psql
*	- import this file: `\i tournament.sql;`
*	- disconnect after database has been created
*******************************************/


-------------------------------------------
-- CREATE new DATABASE instance          --
-------------------------------------------

-- Check for and drop database if exists:
DROP DATABASE IF EXISTS tournament;

-- CREATE and CONNECT to tournament:
CREATE DATABASE tournament;
\c tournament;	


-------------------------------------------
-- CONNECT TO DATABASE and CREATE TABLES --
-------------------------------------------

/*	Table of players.
	
	Columns:
		id: unique id of player (primary key)
		name: name of player
*/
CREATE TABLE players(id SERIAL PRIMARY KEY, 
					 name TEXT);


/*	Table of match results of all tournaments.

	Columns:
		match_id: unique match event (primary key)
		tournament_id: tournament id of given match
		winner_id: id of winning player
		loser_id: id of losing player
*/
CREATE TABLE matches(match_id SERIAL PRIMARY KEY,
					 tournament_id INTEGER,
					 winner_id INTEGER REFERENCES players(id), 
					 loser_id INTEGER REFERENCES players(id));