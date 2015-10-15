<<<<<<< HEAD
/* Create the database tournament */
CREATE DATABASE tournament;

/* Connect to the database */
\c tournament;

/* Create players table - 2 colums */ 
CREATE TABLE players (
        player_id serial PRIMARY KEY,
        name varchar (25)
);

/* Create results table - 3 colums */ 
CREATE TABLE results (
        match_id serial PRIMARY KEY,
        winner integer REFERENCES players(player_id),
        loser integer REFERENCES players(player_id)
);

/* Create standings table: id, name, total wins, total matches played */ 

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
FROM players; 
||||||| merged common ancestors
=======
-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.

CREATE DATABASE tournament; 

CREATE TABLE players (id INTEGER PRIMARY KEY, name TEXT, matches_played INTEGER, wins INTEGER, standing INTEGER); 

-- CREATE TABLE matches (id INTEGER PRIMARY KEY, player1 INT REFERENCES players(id), 
						-- player2 INTEGER REFERENCES players(id));

CREATE TABLE matches (id INTEGER PRIMARY KEY, winner REFERENCES players(id), loser REFERENCES players(id)); 

-- CREATE TABLE player_standings (id INTEGER PRIMARY KEY, name TEXT, standing INTEGER)

-- (id1, name1, wins1, matches1), (id2, name2, wins2, matches2) 

-- create views for the following 
	-- Finding the number of matches each player has played.
CREATE VIEW NUMBER_OF_MATCHES AS SELECT name, matches_played FROM players; 

	-- The number of wins for each player.
CREATE VIEW NUMBER_OF_WINS AS SELECT name, wins FROM players; 

	-- The player standings.
CREATE VIEW PLAYERS_STANDINGS AS SELECT name, standing FROM players; 

INSERT INTO players values("Freddie Mercury", 1, 1, 1), ("Brian May", 1, 1, 1), 
							("Roger Taylor", 1, 0, 2), ("John Deacon", 1, 0, 2);
>>>>>>> c438ae166f3afd9e3cf21a281f88980511b2d5b5
