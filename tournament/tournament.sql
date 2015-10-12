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