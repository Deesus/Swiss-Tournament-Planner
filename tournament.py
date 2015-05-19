import psycopg2
"""
    tournament.py -- implementation of a Swiss-system tournament.

    A database that tracks players and matches in game tournaments.
    Program uses the Swiss-system for pairing players in each round in a
    tournament. Multiple tournaments are supported and players can enter
    multiple tournaments. The database returns players' ranking/standing
    based on wins. In the event that multiple players have the same
    number of wins, ranking is calculated by the Opponent Match Wins.

    API Overview:
        delete_matches(): removes matches from data
        delete_players(): removes players from data
        count_players(tournament_id): counts # of players in given
        tournament
        register_player(name): registers player
        player_standings(tournament_id):  returns the current standings
        report_match(winner, loser, tournament_id): report match results
        swiss_pairings(tournament_id): calculates appropriate match
        pairings


    Quick Start:
        -   Add players into database with register_player() function.
            Function takes string text as a parameter.
        -   Archive match results by reporting them with report_match().
            report_match() takes in winner id and loser id
            (respectively). Optionally, it takes in the tournament id.
        -   swiss_pairings() function will calculate the next pair of
            matchups that satisfies the Swiss-system property.

    To Do -- Future Implementations:
        1)  Maybe just add another table: player's wins, loses -- this
            will make the player_standings() function a lot easier.
        2)  Add features: support for odd-number players; support ties
            as a match result.
        3)  Since matches table is dependant on players table, we could
            call delete_matches() inside delete_players()
"""
__author__ = 'Dee Reddy'


def connect(database_name="tournament"):
    """Connect to PostgreSQL database. Returns connection and cursor."""
    try:
        db = psycopg2.connect("dbname={}".format(database_name))
        cursor = db.cursor()
        return db, cursor
    except:
        print "Error while trying to connect to database"


def delete_matches():
    """Removes all the match records and from database."""

    db, cursor = connect()
    cursor.execute("""TRUNCATE matches;""")
    db.commit()
    db.close()


def delete_players():
    """Removes all the player as well as match records from database."""

    db, cursor = connect()
    cursor.execute("""TRUNCATE players CASCADE;""")
    db.commit()
    db.close()


def count_players(tournament_id=0):
    """Returns the number of players currently registered in selected
    tournament. If no arguments are given, then function returns the
    count of all registered players.

    Args:
        tournament_id: the id (integer) of the tournament.

    Returns:
        An integer of the number of registered players if tournament_id
        is not specified. If tournament_id is specified, returns an
        integer of the number of players in given tournament (who have
        played at least 1 game).
    """

    db, cursor = connect()

    if tournament_id == 0:
        cursor.execute("""SELECT COUNT(id) FROM players;""")
    else:
        cursor.execute("""SELECT CAST(COUNT(subQuery.X) AS INTEGER) FROM
                    (SELECT winner_id AS X
                     FROM matches WHERE matches.tournament_id = %s
                     UNION
                     SELECT loser_id AS X
                     FROM matches WHERE matches.tournament_id = %s)
                     AS subQuery;""", (tournament_id, tournament_id))

    output_ = cursor.fetchone()[0]
    db.close()
    return output_


def register_player(name):
    """Adds a player to the tournament database.

    Args:
        name: the player's full name (need not be unique).
    """

    db, cursor = connect()

    # add player to players table and return its id:
    query = "INSERT INTO players(name) VALUES(%s) RETURNING id;"
    param = (name,)
    cursor.execute(query, param)
    return_id = cursor.fetchone()[0]

    db.commit()
    db.close()
    return return_id


def player_standings(tournament_id=0):
    """Returns a list of the players & their win record, sorted by rank.

    The first entry in the returned list is the person in first place,
    or a player tied for first place if there is currently a tie. Due to
    the requirements of the test cases to return standings before any
    matches have been played, if tournament_id is not specified (i.e.
    tournament_id = 0), the function returns all registered players
    regardless of what tournament they are participating in; otherwise,
    the function returns standings of only the players that have played
    at least 1 game in given tournament_id.

    Args:
        tournament_id: specifies the tournament from which we want the
        results - defaults to 0.

    Returns:
        A list of tuples, each containing (id, name, wins, matches): id:
        the player's unique id (assigned by the database) name: the
        player's full name (as registered) wins: the number of matches
        the player has won matches: the number of matches the player has
        played.
    """

    db, cursor = connect()

    # check how many matches have been played:
    query = """SELECT COUNT(match_id) FROM matches 
               WHERE matches.tournament_id = %s;"""
    param = (tournament_id,)
    cursor.execute(query, param)
    total_matches = cursor.fetchone()[0]

    # if no matches have been played, return registered players:
    if total_matches == 0:
        cursor.execute("""SELECT id, name, 0, 0 FROM players;""")
        output_ = cursor.fetchall()
        db.close()
        return output_

    # Find number of matches played per player:
    cursor.execute("""CREATE OR REPLACE VIEW temp_matches AS
             SELECT players.id, COUNT(players.id)
             AS temp_games_played
             FROM players, matches
             WHERE (players.id = winner_id OR players.id = loser_id)
             AND matches.tournament_id = %s
             GROUP BY players.id;""", (tournament_id,))

    cursor.execute("""CREATE OR REPLACE VIEW num_matches AS
             SELECT DISTINCT subQuery.ID, games_played
             FROM (SELECT players.id AS ID,
                   COALESCE(SUM(temp_games_played), 0)
                   AS games_played
                   FROM players LEFT JOIN temp_matches
                   ON players.id = temp_matches.id
                   GROUP BY players.id)
                   AS subQuery, matches
             WHERE matches.tournament_id = %s
             ORDER BY games_played DESC;""", (tournament_id,))

    # Find number of matches won per player:
    cursor.execute("""CREATE OR REPLACE VIEW games_won AS
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
    cursor.execute("""CREATE OR REPLACE VIEW omw AS
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
    cursor.execute("""SELECT subQuery.id, subQuery.name, wins,
             CAST(games_played AS INTEGER)
             FROM num_matches,
                  (SELECT games_won.id AS id, name,
                   CAST(wins AS INTEGER),
                   COALESCE(opponent_wins, 0) AS opponent_wins
                   FROM games_won LEFT JOIN omw
                   ON id = x)
                   AS subQuery
             WHERE (subQuery.id = num_matches.id) %s
             ORDER BY wins DESC, opponent_wins DESC,
             games_played ASC;""" % tournament_restriction)

    output_ = cursor.fetchall()
    db.close()
    return output_


def report_match(winner, loser, tournament_id=0):
    """Records the outcome of a single match between two players.

    Args:
        winner:  the id number of the player who won
        loser:  the id number of the player who lost
        tournament_id:  the match's tournament id
    """

    db, cursor = connect()

    # Add players into matches table:
    query = "INSERT INTO matches (winner_id, loser_id, tournament_id) \
            VALUES(%s, %s, %s);"
    param = (winner, loser, tournament_id)
    cursor.execute(query, param)

    db.commit()
    db.close()


def swiss_pairings(tournament_id=0):
    """Returns a list of pairs of players for the next round of a match.

    Assuming that there are an even number of players registered, each
    player appears exactly once in the pairings.  Each player is paired
    with another player with an equal or nearly-equal win record, that
    is, a player adjacent to him in the standings.

    Returns:
        A list of tuples, each containing (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """

    standings = player_standings(tournament_id)

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
    # clear data:
    delete_matches()
    delete_players()

    # register players:
    players = ["Dee", "Temur", "Annie", "Adam", "Shikhikhutug",
               "Lakshmi", "Yuji", "Bleda", "Attila", "Marie"]
    p0, p1, p2, p3, p4, p5, p6, p7, p8, p9 = \
        [register_player(x) for x in players]

    # function for printing tests:
    def print_out_test_results(tournament_id):
        print '# of players -- tournament #%s:' % tournament_id
        print count_players(tournament_id), "\n"
        print 'standings -- tournament #%s:' % tournament_id
        print player_standings(tournament_id), "\n"
        print 'swissPairings -- tournament #%s:' % tournament_id
        print swiss_pairings(tournament_id), "\n"

    ##################################################
    # tournament #16:
    # report scores:
    [report_match(x[0], x[1], 16) for x in
     [(p0, p3), (p6, p3), (p6, p1), (p0, p4), (p4, p1)]]

    print_out_test_results(16)
    # expected count: 5
    # expected standings: 'Dee', 'Yuji', 'Shikhikhutug', 'Adam', 'Temur'
    # expected pairings: ('Dee', 'Yuji'), ('Shikhikhutug', 'Adam')

    # more scores to report:
    [report_match(x[0], x[1], 16) for x in
     [(p0, p6), (p4, p3), (p6, p1), (p2, p5), (p0, p4), (p2, p8)]]

    print_out_test_results(16)
    # expected count: 8
    # expected standings: 'Dee', 'Yuji', 'Shikhikhutug', 'Annie',
    # 'Adam', 'Temur', 'Lakshmi', 'Attila'
    # expected pairs: same as standings

    ##################################################
    # tournament #0:
    # standings before any matches:
    print "standings -- tournament #0:"
    print player_standings(), "\n"
    # expected result: all registered players with 0 wins 0 matches

    # report scores:
    [report_match(x[0], x[1]) for x in
     [(p0, p1), (p2, p3), (p3, p1), (p0, p2)]]

    print_out_test_results(0)
    # expected count: 10 -- all registered players
    # expected standings: 'Dee', 'Annie', 'Adam', 'Temur' + remaining
    # expected pairings: ('Dee', 'Annie'), ('Adam', 'Temur') + remaining

    ##################################################
    # clear data:
    delete_matches()
    delete_players()
