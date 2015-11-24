-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.

/* remove previous database data if tournament already exists*/
DROP DATABASE IF EXISTS tournament;

/* Create the database tournament */
CREATE DATABASE tournament;

/* Connect to the database */
\c tournament;

/* Create players table */
CREATE TABLE players (
        player_id serial PRIMARY KEY,
        name varchar (25) NOT NULL
);

/* Create results table */
CREATE TABLE results (
        match_id serial PRIMARY KEY,
        winner integer REFERENCES players(player_id) NOT NULL,
        loser integer REFERENCES players(player_id) NOT NULL
        CHECK (winner <> loser)
);

/* player_id, player name, number of wins, number of matches */
CREATE VIEW standings AS
SELECT players.player_id, players.name,
(SELECT count(results.winner)
    FROM results
    WHERE players.player_id = results.winner)
    AS total_wins,
(SELECT count(results.match_id)
    FROM results
    WHERE players.player_id = results.winner
    OR players.player_id = results.loser)
    AS total_matches
FROM players
ORDER BY total_wins DESC, total_matches DESC;