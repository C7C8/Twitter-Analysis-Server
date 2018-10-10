"""Base data analysis functions"""
import datetime
from twitterscraper.query import query_tweets_from_user
import pymysql

import db
from sentiment import get_text_sentiment


def scrape_user_to_db(username):
	"""Scrape a user and insert everything on them into the database. Will overwrite existing data!"""
	with db.get_db() as cursor:

		tweets = []

		# If we've haven't scraped this user before, do a full scrape. If we have, only get the tweets
		# we don't have yet.
		cursor.execute("SELECT * FROM analyzed_users WHERE username=%s", username)
		if cursor.fetchone() is None:
			cursor.execute("INSERT INTO analyzed_users (username) VALUES (%s)", username)
			tweets = query_tweets_from_user(username, limit=5000)
		else:
			cursor.execute("SELECT checked FROM analyzed_users WHERE username=%s", username)
			d = cursor.fetchone()[0]
			d = d if d is not None else datetime.datetime.utcfromtimestamp(0)

			# If we've already checked this users's tweets within the past day, don't try it again
			if (datetime.datetime.now() - d).days == 0:
				return 0

			cursor.execute("UPDATE analyzed_users SET checked=NOW() WHERE username=%s", username)
			tweets = query_tweets_from_user(username, limit=5000)
			tweets = list(filter(lambda tw: d < tw.timestamp, tweets))

		sql = "INSERT INTO tweets (username, content, created, retweets, favorites, replies, is_retweet, id, sentiment) " \
			  "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
		set_username = False
		for tweet in tweets:
			try:
				# Set the user's full name if it hasn't already been set.
				if not set_username and tweet.user.lower() == username.lower():
					cursor.execute("UPDATE analyzed_users SET fullname=%s WHERE username=%s", (tweet.fullname, username))
					set_username = True

				cursor.execute(sql, (
					username,
					tweet.text,
					tweet.timestamp,
					tweet.retweets,
					tweet.likes,
					tweet.replies,
					tweet.user.lower() != username.lower(),
					tweet.id,
					get_text_sentiment(tweet.text)
				))
			except pymysql.err.IntegrityError:
				pass
		cursor.connection.commit()
		return len(tweets)


def get_tweets_hourly(username):
	"""Get tweets by hour for a given user. Must have already scraped that user into the database."""
	with db.get_db() as cursor:
		ret = [{"total": 0, "total_len": 0, "avg_len": 0, "stdev_len": 0, "avg_send": 0, "stdev_sent": 0} for x in range(24)]
		sql = "SELECT t_hour, total, total_len, avg_len, stdev_len, avg_sent, stdev_sent FROM tweets_hourly_total WHERE username=%s"
		cursor.execute(sql, username)
		hours = cursor.fetchall()
		if hours is None or len(hours) == 0:
			return []

		for hour in hours:
			ret[hour[0]] = {
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
		ret = [{"total": 0, "total_len": 0, "avg_len": 0, "stdev_len": 0, "avg_send": 0, "stdev_sent": 0} for x in range(7)]
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
		ret = [[{"total": 0, "total_len": 0, "avg_len": 0, "stdev_len": 0, "avg_send": 0, "stdev_sent": 0} for x in range(24)] for x in range(7)]
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


def get_tweets_all_time(username):
	"""Get all-time status for a user's tweets"""
	with db.get_db() as cursor:
		sql = "SELECT total, total_len, avg_len, stdev_len, avg_sent, stdev_sent FROM tweets_all WHERE username=%s"
		cursor.execute(sql, username)
		stats = cursor.fetchone()
		if stats is None:
			return None

		return {
			"total": int(stats[0]),
			"total_len": int(stats[1]),
			"avg_len": float(stats[2]),
			"stdev_len": float(stats[3]),
			"avg_sent": float(stats[4]),
			"stdev_sent": float(stats[5])
		}
