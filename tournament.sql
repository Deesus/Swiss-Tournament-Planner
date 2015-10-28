/******************************************
* tournament.py    -- table definitions for the tournament.
*
* Author: Dee Reddy
*
* Quick Start:
*    - import this file: `$ psql -f tournament.sql;`
*    - disconnect after database has been created
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

/*    Table of players.
    
    Columns:
        id: unique id of player (primary key)
        name: name of player
*/
CREATE TABLE players(id SERIAL PRIMARY KEY, 
                     name TEXT);


/*    Table of match results of all tournaments.

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


-------------------------------------------
-- CREATE VIEWS                          --
-------------------------------------------

-- Views used for player_standings:

-- Find number of matches played per player:
CREATE
    OR REPLACE VIEW num_matches AS

SELECT players.id
    ,COALESCE(COUNT(players.id), 0) AS games_played
FROM players
    ,matches
WHERE (
        players.id = winner_id
        OR players.id = loser_id
        )
    AND matches.tournament_id = tournament_id
GROUP BY players.id
ORDER BY games_played DESC;


-- Find number of matches won per player:
CREATE
    OR REPLACE VIEW games_won AS

SELECT players.id AS id
    ,players.NAME
    ,COUNT(subQuery.winner_id) AS wins
FROM players
LEFT JOIN (
    SELECT winner_id
    FROM matches
    WHERE matches.tournament_id = tournament_id
    ) AS subQuery ON players.id = subQuery.winner_id
GROUP BY players.id;


-- Find opponent match wins (omw):
-- (subquery creates 2 columns of id & every opponent he has played)
CREATE
    OR REPLACE VIEW omw AS

SELECT x
    ,CAST(SUM(wins) AS INT) AS opponent_wins
FROM games_won
    ,(
        SELECT winner_id AS x
            ,loser_id AS opponent
        FROM matches
        WHERE matches.tournament_id = tournament_id
        
        UNION
        
        SELECT loser_id AS x
            ,winner_id AS opponent
        FROM matches
        WHERE matches.tournament_id = tournament_id
        ORDER BY x ASC
        ) AS subQuery
WHERE id = opponent
GROUP BY x
ORDER BY x;
