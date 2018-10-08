"""Functions for generating and working with markov chains"""
from functools import reduce

import random
import re
import nltk
import pickle
from sacremoses import MosesDetokenizer

from db import get_db


def get_markov_chain(username, force_new=False):
	"""Returns a markov chain for a given user. If the user hasn't been analyzed yet,
	a new markov chain will be generated and stored in the database. If the user *has*
	been analyzed before, the data from the database will be loaded instead. This data
	is stored as a binary (pickle) for efficiency. If desired a new markov chain can
	be forced."""
	with get_db() as cursor:
		cursor.execute("SELECT chain FROM chains WHERE username=%s", username)
		res = cursor.fetchone()
		if res is None or force_new:
			# Generate a new chain, pickle it, store it in the database, and return it.
			chain = build_markov_chain(username)
			if chain is None:
				return

			chain_binary = pickle.dumps(chain)
			sql = "INSERT INTO chains (username, chain) VALUES (%s, %s)"
			cursor.execute(sql, (username, chain_binary))
			cursor.connection.commit()
			return chain
		else:
			chain = pickle.loads(res[0])
			return chain


def build_markov_chain(username):
	"""Build a markov chain out of data from a user's tweets"""
	with get_db() as cursor:
		cursor.execute(
			"SELECT content FROM tweets WHERE is_retweet = 0 AND username = %s",
			username)
		content = [str(x[0]) for x in cursor.fetchall()]
		if len(content) == 0:
			return

		words = {"START": {"cnt": 0, "dst": {}}, "END": {"cnt": 0, "dst": {}}}
		for tweet in content:
			tweet = sanitize(tweet)
			tweet_words = nltk.tokenize.casual_tokenize(tweet, strip_handles=True, preserve_case=False)

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

		# Now that all data is assembled, calculate probabilities for each individual word
		for word in words.keys():
			dstlist = words[word]["dst"]
			count = sum(int(x) for x in dstlist.values())
			for dst in dstlist.keys():
				words[word]["dst"][dst] = {"cnt": dstlist[dst], "prob": dstlist[dst] / count}

		return words


def sanitize(text):
	# Remove hashtags
	text = re.sub("[#@][\w\d]+", "", text)

	# Remove URLs
	text = re.sub("(http(s)?://)\S+", "", text)
	return re.sub("pic.twitter.com/\S+", "", text)


def prob_list_for_word(word):
	"""Get a probability list for a given word -- it's an easier format to work with
	than a markov chain dictionary"""
	dstlist = word["dst"]
	ret = []
	for dst in dstlist.keys():
		ret.append({"word": dst, "cnt": dstlist[dst]["cnt"], "prob": dstlist[dst]["prob"]})
	return sorted(ret, key=lambda x: -x["prob"])


def all_words_prob(chain):
	"""Get a list of the probabilities (frequency) for each individual word"""
	total_cnt = 0
	ret = []
	for word in chain.keys():
		ret.append({"word": word, "cnt": chain[word]["cnt"]})
		total_cnt = total_cnt + chain[word]["cnt"]
	return sorted([{"word": x["word"], "prob": x["cnt"] / total_cnt, "cnt": x["cnt"]} for x in ret], key=lambda p: -p["prob"])


def get_next_word(chain, word):
	"""Use markov chain data to generate the next word using the last word. Non-deterministic, naturally."""
	if word is None:
		return "END"  # some odd edge case came up...
	prob_map = prob_list_for_word(chain[word])
	selector = random.random()
	total = 0
	for word in prob_map:
		total = total + word["prob"]
		if selector <= total:
			return word["word"]


def generate_tweet(chain, length=0):
	"""Generate a tweet of given length (or until it ends naturally)"""
	detokenizer = MosesDetokenizer()
	size = 1
	sentence = [get_next_word(chain, "START")]
	while length == 0 or length + 2 <= size:
		next_word = get_next_word(chain, sentence[-1])
		if next_word == "END":
			break
		sentence.append(next_word)
	return detokenizer.detokenize(sentence)


def probability_of_fragment(chain, fragment):
	"""Return the probability of a fragment occurring"""
	words = [word.lower() for word in nltk.word_tokenize(fragment)]
	if (words[0]) not in chain.keys():
		return 0
	totalProb = float(chain[words[0]]["prob"])
	for i, word in enumerate(words):
		if i == 0:
			continue
		if words[i] not in chain[words[i-1]]["dst"].keys():
			return 0
		totalProb = totalProb * chain[words[i-1]]["dst"][words[i]]["prob"]
	return totalProb
