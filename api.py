from flask import Flask
from flask_restplus import Api, Resource

app = Flask(__name__)
api = Api(app)
ns = api.namespace("api/twitter", description="Twitter analysis endpoints")


@ns.route("/user")
class ManageUsers(Resource):
	"""Manage users"""

	def get(self):
		"""Gets list of analyzed users."""
		pass

	def put(self):
		"""Add a new user to be analyzed. Returns number of tweets fetched."""
		pass


@ns.route("/analyze")
class Analysis(Resource):
	"""Get analyses of users"""

	def get(self):
		"""Get different analyses for user, depending on parameters"""
		pass


@ns.route("/generate")
class Generate(Resource):
	"""Generate tweets for a given user"""

	def get(self):
		"""Get an arbitrary number of tweets from a given user (assuming they've been analyzed)"""
		pass


if __name__ == "__main__":
	app.run()
