"""Scrape tweets from Twitter using twitterscraper and shove them into the database"""
from datetime import datetime

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


def get_tweets_by_day(username):
	"""Get tweets by day for a given user. Must have already scraped that user into the database."""
	with db.get_db() as cursor:
		ret = []
		sql = "SELECT t_date, total, total_len, avg_len, stdev_len FROM tweets_daily WHERE username=%s"
		cursor.execute(sql, username)
		days = cursor.fetchall()
		if days is None or len(days) == 0:
			return []

		for day in days:
			ret.append({
				"date": day[0],
				"total": int(day[1]),
				"total_len": int(day[2]),
				"avg_len": float(day[3]),
				"stdev_len": float(day[4])
			})
		return sorted(ret, key=lambda x: x["date"])


def get_tweets_hourly(username):
	"""Get tweets by hour for a given user. Must have already scraped that user into the database."""
	with db.get_db() as cursor:
		ret = []
		sql = "SELECT t_hour, total, total_len, avg_len, stdev_len FROM tweets_hourly_total WHERE username=%s"
		cursor.execute(sql, username)
		hours = cursor.fetchall()
		if hours is None or len(hours) == 0:
			return []

		for hour in hours:
			ret.append({
				"hour": int(hour[0]),
				"total": int(hour[1]),
				"total_len": int(hour[2]),
				"avg_len": float(hour[3]),
				"stdev_len": float(hour[4])
			})

		return sorted(ret, key=lambda x: x["hour"])
