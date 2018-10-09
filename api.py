import nltk
from flask import Flask
from flask_restplus import Api, Resource, reqparse

import data
import db
from markov import get_markov_chain, generate_tweet, sanitize, probability_of_fragment, get_next_word

app = Flask(__name__)
api = Api(app)
ns = api.namespace("api/twitter", description="Twitter analysis endpoints")


@ns.route("/users")
class ManageUsers(Resource):
	"""Manage users"""

	def get(self):
		"""Gets list of analyzed users."""
		return {
			"status": "success",
			"message": "Found user list",
			"users": db.get_analyzed_users()
		}, 200

	def put(self):
		"""Add a new user to be analyzed. Returns number of tweets fetched."""
		parser = reqparse.RequestParser()
		parser.add_argument("username", type=str, required=True)
		args = parser.parse_args()
		count = data.scrape_user_to_db(args["username"])
		get_markov_chain(args["username"])
		if count == 0:
			return response(True, "Didn't scrape any more tweets for " + args["username"], "count", 0), 200
		else:
			return response(True, "Scraped tweets for " + args["username"], "count", count), 200


@ns.route("/analyze")
class Analysis(Resource):
	"""Get analyses of users"""

	def get(self):
		"""Get different analyses for user, depending on parameters"""
		parser = reqparse.RequestParser()
		parser.add_argument("username", type=str, required=True)
		parser.add_argument("analysis", type=str, required=True)
		args = parser.parse_args()
		if args["analysis"] not in ["alltime", "hourly", "weekly", "hourly_daily"]:
			return response(False, "Bad analysis type"), 400

		username = args["username"]
		action = args["analysis"]
		analysis = None
		if action == "alltime":
			analysis = data.get_tweets_all_time(username)
		elif action == "hourly":
			analysis = data.get_tweets_hourly(username)
		elif action == "weekly":
			analysis = data.get_tweets_weekly(username)
		elif action == "hourly_daily":
			analysis = data.get_tweets_hourly_by_day(username)

		if analysis is not None:
			return response(True, "Analysis performed", "data", analysis), 200
		else:
			return response(False, "Failed to find user or tweets to operate on"), 400


@ns.route("/generate")
class Generate(Resource):
	"""Generate tweets for a given user, or analyze existing text for probability"""

	def get(self):
		parser = reqparse.RequestParser()
		parser.add_argument("username", type=str, required=True)
		parser.add_argument("count", type=int, required=True)
		args = parser.parse_args()
		if args["count"] < 1:
			return response(False, "Must request at least one tweet")

		chain = get_markov_chain(args["username"])
		if chain is None:
			return response(False, "User " + args["username"] + " not analyzed yet"), 400

		tweets = [generate_tweet(chain) for x in range(args["count"])]
		return response(True, str(args["count"]) + " tweets generated", "tweets", tweets) , 200


@ns.route("/probability")
class Probability(Resource):
	"""Calculate probability for sentence fragment"""

	def get(self):
		parser = reqparse.RequestParser()
		parser.add_argument("username", type=str, required=True)
		parser.add_argument("text", type=str, required=True)
		args = parser.parse_args()

		chain = get_markov_chain(args["username"])
		sentence = nltk.tokenize.casual_tokenize(sanitize(args["text"]), preserve_case=False)
		if chain is None:
			return response(False, "User " + args["username"] + " not analyzed yet"), 400

		return {
			"status": "success",
			"message": "Analysis follows",
			"probability": probability_of_fragment(chain, args["text"]),
			"next_word": get_next_word(chain, sentence[-1])
		}, 200


def response(success, message, descriptor=None, payload=None):
	"""Helper to generate standard format API responses"""
	if descriptor is None:
		return {"status": "success" if success else "error", "message": message}
	else:
		return {"status": "success" if success else "error", "message": message, descriptor: payload}


if __name__ == "__main__":
	app.run()
