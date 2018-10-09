"""Database utilities"""
import json
import pymysql


def get_db():
	# Backup settings in case conf.json can't be found
	conf = {
		"host": "localhost",
		"port": 3306,
		"user": "tweets",
		"password": "password",
		"database": "database"
	}
	try:
		with open("conf.json", "r") as file:
			conf = json.loads(file.read())["db"]
	except FileNotFoundError:
		print("Couldn't load database config from conf.json, switching to default config")

	connection = pymysql.connect(**conf)
	return connection.cursor()


def get_analyzed_users():
	"""Get list of analyzed users -- their username and real name together in a dict"""
	with get_db() as cursor:
		cursor.execute("SELECT username, fullname FROM analyzed_users")
		return [{"username": res[0], "fullname": res[1]} for res in cursor.fetchall()]
