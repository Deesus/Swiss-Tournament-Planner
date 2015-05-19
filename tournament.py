"""
    tournament.py -- implementation of a Swiss-system tournament.

    A database that tracks players and matches in game tournaments. Program
    uses the Swiss-system for pairing players in each round in a tournament.
    Multiple tournaments are supported and players can enter multiple
    tournaments. The database returns players' ranking/standing based on wins.
    In the event that multiple players have the same number of wins, ranking is
    calculated by the Opponent Match Wins (OMW).

    API Overview:
        deleteMatches():  removes matches from data
        deletePlayers():  removes players from data
        countPlayers(tournament_id):  counts # of players in given tournament
        registerPlayer(name):  registers player
        playerStandings(tournament_id):  returns the current standings
        reportMatch(winner, loser, tournament_id):  report match results 
        swissPairings(tournament_id):  calculates appropriate match pairings
        

    Quick Start:
        -   Add players into database with registerPlayer() function. 
            Function takes string text as a parameter.
        -   Archive match results with by reporting them with reportMatch().
            reportMatch() takes in winner id and loser id (respectively).
            Optionally, it takes in the tournament's id.
        -   swissPairings() function will calculate the next pair of matchups
            that satisfies the Swiss-system property.
        
    To Do: 
        1)  Maybe just add another table: player's wins, loses -- this will make
            the playerStandings() function a lot easier.
        2)  Perhaps save the wins/loss as a view in tournament.sql (rather than
            in tournament.py) and update when needed.
        3)  Is tournament_restriction in playerStandings() function necessary?
            Perhaps we should just return all players regardless of tournament
            participation.
        4)  Add features: support for odd-number players; support ties as a
            match result.
        5)  Since matches table is dependant on players table, we could call
            deleteMatches() inside deletePlayers()
"""
__author__ = 'Dee Reddy'

import psycopg2


def connect():
    """Connect to the PostgreSQL database. Returns a connection."""

    return psycopg2.connect("dbname=tournament")


def deleteMatches():
    """Remove all the match records and tournament_entries from the
    database.
    """

    pg = connect()
    c = pg.cursor()
    c.execute("DELETE FROM matches;")
    pg.commit()
    pg.close()


def deletePlayers():
    """Remove all the player records and tournament_entries from the database.
    """

    pg = connect()
    c = pg.cursor()
    c.execute("DELETE FROM players;")
    pg.commit()
    pg.close()


def countPlayers(tournament_id=0):
    """Returns the number of players currently registered in selected
    tournament. If no arguments are given, then function returns the count of
    all registered players.

    Args:
        tournament_id: the id (integer) of the tournament.

    Returns:
        An integer of the number of registered players if tournament_id is not
        specified. If tournament_id is specified, returns an integer of the
        number of players in given tournament (who have played at least 1 game).
    """

    pg = connect()
    c = pg.cursor()

    if tournament_id == 0:
        c.execute("""SELECT COUNT(id) FROM players;""")
    else:
        c.execute("""SELECT CAST(COUNT(subQuery.X) AS INTEGER) FROM
                    (SELECT winner_id AS X
                     FROM matches WHERE matches.tournament_id = %s
                     UNION 
                     SELECT loser_id AS X
                     FROM matches WHERE matches.tournament_id = %s)
                     AS subQuery;""", (tournament_id, tournament_id))

    output_ = c.fetchone()[0]
    pg.close()
    return output_


def registerPlayer(name):
    """Adds a player to the tournament database.

    Args:
        name: the player's full name (need not be unique).
    """

    pg = connect()
    c = pg.cursor()

    # add player to players table and return its id:
    c.execute("""INSERT INTO players(name)
                 VALUES(%s) RETURNING id;""", (name,))
    return_id = c.fetchone()[0]

    pg.commit()
    pg.close()
    return return_id


def playerStandings(tournament_id=0):
    """Returns a list of the players & their win record, sorted by rank.

    The first entry in the returned list is the person in first place, or a
    player tied for first place if there is currently a tie. Due to the
    requirements of the test cases to return standings before any matches have
    been played, if tournament_id is not specified (i.e. tournament_id = 0), the
    function returns all registered players regardless of what tournament they
    are participating in; otherwise, the function returns standings of only the
    players that have played at least 1 game in given tournament_id.

    Args:
        tournament_id: specifies the tournament from which we want the
        results - defaults to 0.

    Returns:
        A list of tuples, each containing (id, name, wins, matches): id: the
        player's unique id (assigned by the database) name: the player's full
        name (as registered) wins: the number of matches the player has won
        matches: the number of matches the player has played
    """

    pg = connect()
    c = pg.cursor()

    # check how many matches have been played:
    c.execute("""SELECT COUNT(match_id) FROM matches
                 WHERE matches.tournament_id = %s;""", (tournament_id,))
    total_matches = c.fetchone()[0]

    # if no matches have been played, return registered players:
    if total_matches == 0:
        c.execute("""SELECT id, name, 0, 0 FROM players;""")
        output_ = c.fetchall()
        pg.close()
        return output_

    # Find number of matches played:
    c.execute("""CREATE VIEW temp_matches AS
                 SELECT players.id, COUNT(players.id) AS temp_games_played
                 FROM players, matches
                 WHERE (players.id = winner_id OR players.id = loser_id)
                 AND matches.tournament_id = %s
                 GROUP BY players.id;""", (tournament_id,))

    c.execute("""CREATE VIEW num_matches AS
                 SELECT DISTINCT subQuery.ID, games_played
                 FROM (SELECT players.id AS ID,
                       COALESCE(SUM(temp_games_played), 0) AS games_played
                       FROM players LEFT JOIN temp_matches
                       ON players.id = temp_matches.id
                       GROUP BY players.id)
                       AS subQuery, matches
                 WHERE matches.tournament_id = %s
                 ORDER BY games_played DESC;""", (tournament_id,))

    # Find number of matches won:
    c.execute("""CREATE VIEW games_won AS
                 SELECT players.id as id, players.name,
                 COUNT(subQuery.winner_id) AS wins
                 FROM players LEFT JOIN (SELECT winner_id
                                         FROM matches
                                         WHERE matches.tournament_id = %s)
                                         AS subQuery
                 ON players.id = subQuery.winner_id
                 GROUP BY players.id;""", (tournament_id,))

    # Find opponent match wins (omw):
    # (subquery creates 2 columns of id & every opponent he has played)
    c.execute("""CREATE VIEW omw AS
                 SELECT x, CAST(SUM(wins) AS INTEGER) AS opponent_wins
                 FROM games_won, (SELECT winner_id AS x, loser_id
                                  AS opponent FROM matches
                                  WHERE matches.tournament_id = %s
                                  UNION
                                  SELECT loser_id AS x, winner_id
                                  AS opponent FROM matches
                                  WHERE matches.tournament_id = %s
                                  ORDER BY x ASC)
                                  AS subQuery
                 WHERE id = opponent
                 GROUP BY x
                 ORDER BY x;""", (tournament_id, tournament_id))

    # Joins tables and returns standings -- sorted by wins, omw:
    # if tournament_id is specified, returns only players that have
    # played in that specific tournament:
    if tournament_id != 0:
        tournament_restriction = 'AND games_played > 0'
    else:
        tournament_restriction = ''
    # (subquery combines wins-count data with opponent wins (omw) &
    # select number of games played)
    c.execute("""SELECT subQuery.id, subQuery.name, wins,
                 CAST(games_played AS INTEGER)
                 FROM num_matches,
                      (SELECT games_won.id AS id, name, CAST(wins AS INTEGER),
                       COALESCE(opponent_wins, 0) AS opponent_wins
                       FROM games_won LEFT JOIN omw
                       ON id = x)
                       AS subQuery
                 WHERE (subQuery.id = num_matches.id) %s
                 ORDER BY wins DESC, opponent_wins DESC, games_played ASC;"""
                 % tournament_restriction)

    output_ = c.fetchall()
    pg.close()
    return output_


def reportMatch(winner, loser, tournament_id=0):
    """Records the outcome of a single match between two players.

    Args:
        winner:  the id number of the player who won
        loser:  the id number of the player who lost
        tournament_id:  the id of the tournament that the match was played
    """

    pg = connect()
    c = pg.cursor()

    # Add players into matches table:
    c.execute("""INSERT INTO matches(winner_id, loser_id, tournament_id)
                 VALUES(%s, %s, %s);""", (winner, loser, tournament_id))

    pg.commit()
    pg.close()


def swissPairings(tournament_id=0):
    """Returns a list of pairs of players for the next round of a match.

    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him in the standings.

    Returns:
        A list of tuples, each containing (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """

    standings = playerStandings(tournament_id)

    pairings = []
    iii = 1
    while iii < len(standings):
        tup1 = standings[iii-1]
        tup2 = standings[iii]

        pairings.append(tuple((tup1[0], tup1[1], tup2[0], tup2[1])))
        iii += 2

    return pairings


#############################
#        test client        #
#############################

if __name__ == "__main__":
    # clear content:
    deleteMatches()
    deletePlayers()

    # register players:
    players = ["Dee", "Temur", "Annie", "Adam", "Shikhikhutug", 
               "Lakshmi", "Yuji", "Bleda", "Attila", "Marie"]
    p0, p1, p2, p3, p4, p5, p6, p7, p8, p9 = \
        [registerPlayer(x) for x in players]

    ##################################################
    # tournament #16 scores:
    reportMatch(p0, p3, 16); reportMatch(p6, p3, 16)
    reportMatch(p6, p1, 16); reportMatch(p0, p4, 16)
    reportMatch(p4, p1, 16);

    print "# of players -- tournament #16:"
    print countPlayers(16); print
    # expected count: 5

    print "standings -- tournament #16:"
    print playerStandings(16); print
    # expected standings: 'Dee', 'Yuji', 'Shikhikhutug', 'Adam', 'Temur'

    print "swissPairings -- tournament #16:"
    print swissPairings(16); print
    # expected pairings: ('Dee', 'Yuji'), ('Shikhikhutug', 'Adam')

    # more tournament #16 scores:
    reportMatch(p0, p6, 16); reportMatch(p4, p3, 16);
    reportMatch(p6, p1, 16); reportMatch(p2, p5, 16);
    reportMatch(p0, p4, 16); reportMatch(p2, p8, 16);

    print "# of players -- tournament #16:"
    print countPlayers(16); print
    # expected count: 8

    print "standings -- tournament #16:"
    print playerStandings(16); print
    # expected standings: 'Dee', 'Yuji', 'Shikhikhutug', 'Annie',
    # 'Adam', 'Temur', 'Lakshmi', 'Attila'

    print "swissPairings -- tournament #16:"
    print swissPairings(16); print
    # expected pairs: same as standings

    ##################################################
    # standings before any matches:
    print "standings -- tournament #0:"
    print playerStandings(); print
    # expected result: all registered players with 0 wins 0 matches

    # tournament #0 scores:
    reportMatch(p0, p1); reportMatch(p2, p3)
    reportMatch(p3, p1); reportMatch(p0, p2)

    print "# of players -- tournament #0:"
    print countPlayers(); print
    # expected count: 10 -- all registered players

    print "standings -- tournament #0:"
    print playerStandings(); print
    # expected standings: 'Dee', 'Annie', 'Adam', 'Temur' + remaining players

    print "swissPairings -- tournament #0:"
    print swissPairings(); print
    # expected pairings: ('Dee', 'Annie'), ('Adam', 'Temur') + remaining players

    ##################################################
    # clear content:
    deleteMatches()
    deletePlayers()