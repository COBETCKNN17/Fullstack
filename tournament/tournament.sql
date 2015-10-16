-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.

/* Create the database tournament */
CREATE DATABASE tournament;

/* Connect to the database */
\c tournament;

/* Create players table */
CREATE TABLE players (
        player_id serial PRIMARY KEY,
        name varchar (25) 
);

/* Create results table */
CREATE TABLE results (
        match_id serial PRIMARY KEY,
        winner integer REFERENCES players(player_id),
        loser integer REFERENCES players(player_id)
);

/* Create view to track match prorgres*/
/* player_id, player name, number of matches, number of wins*/
CREATE VIEW standings AS
SELECT players.player_id, players.name,
(SELECT count(results.match_id)
    FROM results
    WHERE players.player_id = results.winner
    OR players.player_id = results.loser)
    AS total_matches
(SELECT count(results.winner)
    FROM results
    WHERE players.player_id = results.winner)
    AS total_wins,
FROM players
ORDER BY total_wins DESC, total_matches DESC;