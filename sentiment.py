from nltk.sentiment.vader import SentimentIntensityAnalyzer

from db import get_db


def get_text_sentiment(sentence):
	"""Get a sentence's score using VADER"""
	analyzer = SentimentIntensityAnalyzer()
	return analyzer.polarity_scores(sentence)["compound"]


def get_user_sentiment_average(username):
	"""Get a user's average sentiment"""
	with get_db() as cursor:
		cursor.execute("SELECT AVG(sentiment) FROM tweets WHERE username=%s AND is_retweet=0", username)
		return cursor.fetchone()[0]
