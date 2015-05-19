/******************************************
* Table definitions for the tournament project.
*
* Author: Dee Reddy
*
* Quick Start:
* 	If database has not been initialized or has been dropped,
*	you can setup the tournament database by importing this file.
*
*******************************************/


-------------------------------------------
-- CREATE DATABASE tournament in psql, and connect to tournament
-------------------------------------------

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
		match_id:
		tournament_id: 
		winner_id:
		loser_id:
*/
CREATE TABLE matches(match_id SERIAL PRIMARY KEY,
					 tournament_id INTEGER,
					 winner_id INTEGER REFERENCES players(id), 
					 loser_id INTEGER REFERENCES players(id));