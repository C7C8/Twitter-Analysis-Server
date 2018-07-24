import pymysql
import html
import dateutil
import json
import re
import nltk


def get_db():
    with open("db_conf.json", "r") as file:
        conf = json.loads(file.read())

    connection = pymysql.connect(
        host=conf["host"],
        port=conf["port"],
        user=conf["user"],
        password=conf["password"],
        database=conf["schema"]
    )
    return connection, connection.cursor()


def load_from_json(filename, cursor, connection):
    """Loadd tweets from a JSON file and insert them into the base_tweets table"""
    with open(filename, "r") as file:
        json_tweets = json.loads(file.read())

    cnt = 0
    for tweet in json_tweets:
        cnt = cnt + 1
        if cnt % 1000 == 0:
            print(str(int(cnt * 100 / len(json_tweets))) + "% complete")
        sql = "INSERT INTO trump.base_tweets(source, content, created, rewteets, favorites, is_retweet, id)" \
              "VALUES(%s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(sql, (
            tweet["source"],
            html.unescape(tweet["text"]),
            dateutil.parser.parse(tweet["created_at"]),
            int(tweet["retweet_cnt"]),
            int(tweet["favorite_cnt"]),
            1 if tweet["is_retweet"] else 0,
            int(tweet["id_str"])
        ))
    connection.commit()


def build_markov_chain(cursor, connection):
    """Build a markov chain and store it in the relevant tables"""
    # Fetch list of all tweets from db
    cursor.execute(
        "SELECT content FROM base_tweets WHERE (source = 'Twitter for iPhone' OR source = 'Twitter for Android')  AND is_retweet = 0 "
        "AND YEAR(created) >= 2015")
    content = [str(x[0]) for x in cursor.fetchall()]

    words = {"START": {"cnt": 0, "dst": {}}, "END": {"cnt": 0, "dst": {}}}
    for tweet in content:
        # Remove hashtags
        tweet = re.sub("[#@][\w\d]+", "", tweet)

        # Remove URLs
        tweet = re.sub("(http(s)?://)?[^\s]*\.co(m)?(/[^\s]*)?", "", tweet)

        # Tokenize with NLTK
        tweet_words = [word.lower() for word in nltk.tokenize.word_tokenize(tweet)]

        # Parent the first word in the tweet to START
        if len(tweet_words) > 0:
            cur = words["START"]
            cur["cnt"] = cur["cnt"] + 1
            if tweet_words[0] in cur["dst"].keys():
                cur["dst"][tweet_words[0]] = cur["dst"][tweet_words[0]] + 1
            else:
                cur["dst"][tweet_words[0]] = 1
            words["START"] = cur

        for index, word in enumerate(tweet_words):
            # Increase cnt of this word by one
            if word not in words.keys():
                words[word] = {"cnt": 1, "dst": {}}
            else:
                words[word]["cnt"] = words[word]["cnt"] + 1

            # Set the next word in the tweet (or END if this is the last word) to be this word's child
            cur = words[word]
            child_word = tweet_words[index + 1] if index != len(tweet_words) - 1 else "END"
            if child_word in cur["dst"].keys():
                cur["dst"][child_word] = cur["dst"][child_word] + 1
            else:
                cur["dst"][child_word] = 1
            words[word] = cur

    sql_node = "INSERT INTO markov_nodes(word, cnt) VALUES (%s, %s)"
    sql_link = "INSERT INTO markov_link(src, dst, cnt, probability) VALUES (%s, %s, %s, %s)"

    # Insert words
    for word in words.keys():
        try:
            cursor.execute(sql_node, (word, words[word]["cnt"]))
        except pymysql.IntegrityError:
            print("DUPLICATE WORD: " + word)

    # Insert links
    for word in words.keys():
        for link in words[word]["dst"].keys():
            try:
                cursor.execute(sql_link,
                               (word, link, words[word]["dst"][link], words[word]["dst"][link] / words[word]["cnt"]))
            except pymysql.IntegrityError:
                print("DUPLICATE LINK: " + word + ", " + link)

    connection.commit()
    print("Added " + str(len(words)) + " words to the db")


def get_markov_chain(cursor):
    """Reconstitute the markov chain stored in db tables"""
    chain = {}
    cursor.execute("SELECT SUM(cnt) FROM markov_nodes")
    total = float(cursor.fetchone()[0])
    cursor.execute("SELECT * FROM markov_nodes")
    results = cursor.fetchall()
    for entry in results:
        chain[entry[0]] = {"cnt": entry[1], "prob": entry[1] / total, "dst": {}}

    cursor.execute("SELECT * FROM markov_link")
    results = cursor.fetchall()
    for link in results:
        chain[link[0]]["dst"][link[1]] = {"cnt": link[2], "prob": link[3]}

    return chain


def prob_list_for_word(word):
    dstlist = word["dst"]
    ret = []
    for dst in dstlist.keys():
        ret.append({"word": dst, "cnt": dstlist[dst]["cnt"], "prob": dstlist[dst]["prob"]})
    return sorted(ret, key=lambda x: -x["prob"])


def all_words_prob(chain):
    total_cnt = 0
    ret = []
    for word in chain.keys():
        ret.append({"word": word, "cnt": chain[word]["cnt"]})
        total_cnt = total_cnt + chain[word]["cnt"]
    return sorted([{"word": x["word"], "prob": x["cnt"] / total_cnt, "cnt": x["cnt"]} for x in ret],
                  key=lambda p: -p["prob"])
