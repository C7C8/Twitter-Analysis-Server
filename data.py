"""Scrape tweets from Twitter using twitterscraper and shove them into the database"""
from datetime import datetime

import twitterscraper

import db
from sentiment import get_text_sentiment


def scrape_user_to_db(username):
	"""Scrape a user and insert everything on them into the database. Will overwrite existing data!"""
	tweets = twitterscraper.query_tweets("from:" + username, 5000)
	if len(tweets) == 0:
		return
	with db.get_db() as cursor:

		# Drop every existing tweet we have on the user so we can do a full insert later.
		# TODO: Optimize so instead only tweets we don't have are fetched
		cursor.execute("DELETE FROM analyzed_users WHERE username=%s", tweets[0].user)
		cursor.execute("INSERT INTO analyzed_users (username, fullname) VALUES (%s, %s)",
					   (username, tweets[0].fullname))

		sql = "INSERT INTO tweets (username, content, created, retweets, favorites, replies, is_retweet, id, sentiment) " \
			  "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
		for tweet in tweets:
			cursor.execute(sql, (
				username,
				tweet.text,
				tweet.timestamp,
				tweet.retweets,
				tweet.likes,
				tweet.replies,
				tweet.user != username,
				tweet.id,
				get_text_sentiment(tweet.text)
			))
		cursor.connection.commit()


def get_tweets_by_day(username):
	"""Get tweets by day for a given user. Must have already scraped that user into the database."""
	with db.get_db() as cursor:
		ret = []
		sql = "SELECT t_date, total, total_len, avg_len, stdev_len, avg_sent, stdev_sent FROM tweets_daily WHERE username=%s"
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
				"stdev_len": float(day[4]),
				"avg_sent": float(day[5]),
				"stdev_sent": float(day(6))
			})
		return sorted(ret, key=lambda x: x["date"])


def get_tweets_hourly(username):
	"""Get tweets by hour for a given user. Must have already scraped that user into the database."""
	with db.get_db() as cursor:
		ret = [{"total": 0, "total_len": 0, "avg_len": 0, "stdev_len": 0} for x in range(24)]
		sql = "SELECT t_hour, total, total_len, avg_len, stdev_len, avg_sent, stdev_sent FROM tweets_hourly_total WHERE username=%s"
		cursor.execute(sql, username)
		hours = cursor.fetchall()
		if hours is None or len(hours) == 0:
			return []

		for hour in hours:
			ret[hour[0]] = {
				"hour": int(hour[0]),
				"total": int(hour[1]),
				"total_len": int(hour[2]),
				"avg_len": float(hour[3]),
				"stdev_len": float(hour[4]),
				"avg_sent": float(hour[5]),
				"stdev_sent": float(hour[6])
			}

		return ret


def get_tweets_weekly(username):
	"""Get tweets by weekday for a given user. Must have already scraped that user into the database. Returned as
	an array with array[day] structure"""
	with db.get_db() as cursor:
		ret = [{"total": 0, "total_len": 0, "avg_len": 0, "stdev_len": 0} for x in range(7)]
		sql = "SELECT t_weekday, total, total_len, avg_len, stdev_len, avg_sent, stdev_sent FROM tweets_weekly WHERE username=%s"
		cursor.execute(sql, username)
		weekdays = cursor.fetchall()
		if weekdays is None or len(weekdays) == 0:
			return []

		for day in weekdays:
			ret[day[0]] = {
				"total": int(day[1]),
				"total_len": int(day[2]),
				"avg_len": float(day[3]),
				"stdev_len": float(day[4]),
				"avg_sent": float(day[5]),
				"stdev_sent": float(day[6])
			}
		return ret


def get_tweets_hourly_by_day(username):
	"""Get tweets hourly on a weekday basis (e.g. 2 tweets a 5 PM on a Monday). Must have already scraped that user
	into the database. Returned as a 2D array, with array[day][hour] structure"""
	with db.get_db() as cursor:
		ret = [[{"total": 0, "total_len": 0, "avg_len": 0, "stdev_len": 0} for x in range(24)] for x in range(7)]
		sql = "SELECT t_hour, t_day, total, total_len, avg_len, stdev_len, avg_sent, stdev_sent FROM tweets_hourly_by_day WHERE username=%s"
		cursor.execute(sql, username)
		hours = cursor.fetchall()
		if hours is None or len(hours) == 0:
			return []

		for hour in hours:
			ret[hour[1]][hour[0]] = {
				"total": int(hour[2]),
				"total_len": int(hour[3]),
				"avg_len": float(hour[4]),
				"stdev_len": float(hour[5]),
				"avg_sent": float(hour[6]),
				"stdev_sent": float(hour[7])
			}
		return ret
