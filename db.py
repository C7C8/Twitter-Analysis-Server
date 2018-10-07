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
