import re
import nltk

from db import get_db


def build_markov_chain(username):
	"""Build a markov chain out of data from a user's tweets"""
	# Fetch list of all tweets from db
	with get_db() as cursor:
		cursor.execute(
			"SELECT content FROM tweets WHERE (source = 'Twitter for iPhone' OR source = 'Twitter for Android' " \
			"AND is_retweet = 0 AND username = %s)",
			username)
		content = [str(x[0]) for x in cursor.fetchall()]

		words = {"START": {"cnt": 0, "dst": {}}, "END": {"cnt": 0, "dst": {}}}
		for tweet in content:
			# Remove hashtags
			tweet = re.sub("[#@][\w\d]+", "", tweet)

			# Remove URLs
			tweet = re.sub("(http(s)?://)?[^\s]*\.co(m)?(/[^\s]*)?", "", tweet)

			# Tokenize with NLTK
			tweet_words = [word.lower() for word in nltk.tokenize.word_tokenize(tweet)]

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

		return words


def prob_list_for_word(word):
	dstlist = word["dst"]
	ret = []
	for dst in dstlist.keys():
		ret.append({"word": dst, "cnt": dstlist[dst]["cnt"], "prob": dstlist[dst]["prob"]})
	return sorted(ret, key=lambda x: -x["prob"])


def all_words_prob(chain):
	total_cnt = 0
	ret = []
	for word in chain.keys():
		ret.append({"word": word, "cnt": chain[word]["cnt"]})
		total_cnt = total_cnt + chain[word]["cnt"]
	return sorted([{"word": x["word"], "prob": x["cnt"] / total_cnt, "cnt": x["cnt"]} for x in ret], key=lambda p: -p["prob"])
