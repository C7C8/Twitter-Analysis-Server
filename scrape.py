"""Scrape tweets from Twitter using twitterscraper and shove them into the database"""

import twitterscraper

import db


def scrape_user_to_db(username):
	"""Scrape a user and insert everything on them into the database. Will overwrite existing data!"""
	tweets = twitterscraper.query_tweets(username)
	if len(tweets) == 0:
		return
	with db.get_db() as cursor:

		# Drop every existing tweet we have on the user so we can do a full insert later.
		# TODO: Optimize so instead only tweets we don't have are fetched
		print(tweets[0].user)
		cursor.execute("DELETE FROM tweets WHERE username=%s", tweets[0].user)
		cursor.execute("INSERT INTO analyzed_users (username, fullname) VALUES (%s, %s)",
					   (username, tweets[0].fullname))

		sql = "INSERT INTO tweets (username, content, created, retweets, favorites, replies, is_retweet, id) " \
			  "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
		for tweet in tweets:
			cursor.execute(sql, (
				username,
				tweet.text,
				tweet.timestamp,
				tweet.retweets,
				tweet.likes,
				tweet.replies,
				tweet.user != username,
				tweet.id))
		cursor.connection.commit()
