#!/usr/bin/env python
#
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2


def connect(database_name="tournament"):

    """Creates database connection and cursor object, throws exception if
    there is a connection error"""

    try:
        db_connect = psycopg2.connect("dbname={}".format(database_name))
        cursor = db_connect.cursor()
        return db_connect, cursor
    except:
        print "Cannot db_connect to database"


def deleteMatches():
    """Remove all the match records from the database."""
    "Connect to the database, create cursor, execute sql query, commit, close connection"
    db, cursor = connect()
    query = "DELETE FROM results;"
    cursor.execute(query)
    db.commit()
    db.close()


def deletePlayers():
    """Remove all the player records from the database."""
    db, cursor = connect()
    query = "DELETE FROM players;"
    cursor.execute(query)
    db.commit()
    db.close()

def countPlayers():
    """Returns the number of players currently registered."""
    db, cursor = connect()
    query = "SELECT count(player_id) as player_count FROM players;"
    cursor.execute(query)
    player_count = cursor.fetchone()[0]
    db.close()
    return player_count

def registerPlayer(name):
    """Adds a player to the tournament database.

    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)

    Args:
      name: the player's full name (need not be unique).
    """
    db, cursor = connect()
    query = "INSERT INTO players(player_id, name) VALUES(default, %s);"
    cursor.execute(query, (name,))
    db.commit()
    db.close()


def playerStandings():
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """
    db, cursor = connect()
    query = "SELECT player_id, name, total_wins, total_matches FROM standings;"
    cursor.execute(query)
    standings = cursor.fetchall()
    db.close()
    return standings


def reportMatch(winner, loser):

    """Records the outcome of a single match between two players.
    Args:
      winner:  player_id of the player who won
      loser:  player_id of the player who lost
    'query' stores the postgresql commands to be executed by the
    cursor object which inserts a player name and id as winner
    and loser, into the results table.
    db_connect() commits changes and closes the database.
    """

    db, cursor = connect()
    query = ("INSERT INTO results(match_id, winner, loser) \
              VALUES (default, %s, %s);")
    cursor.execute(query, (winner, loser,))
    db.commit()
    db.close()

def swissPairings():
    """Returns a list of pairs of players for the next round of a match.

    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.

    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """
    pair = []
    db, cursor = connect()
    # fetching player_id and name to match them into pairs
    cursor.execute("SELECT player_id, name FROM standings \
                    ORDER BY total_wins DESC;")
    # assigning results of query to a tuple
    winning_pairs = cursor.fetchall()
    # checking if the length of the tuple is even - indicating all results can be paired
    if len(winning_pairs) % 2 == 0:
        # create pairs by looping through the results of the tuple
        for i in range(0, len(winning_pairs), 2):
            collect_players = winning_pairs[i][0], winning_pairs[i][1], \
                              winning_pairs[i+1][0], winning_pairs[i+1][1]
            pair.append(collect_players)
        return pair

    else:
        print "There are an uneven number of players in the tournament"
        return pair

    db.close()
