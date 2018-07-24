#!/usr/bin/python
import sys
import nltk
from tweets_util import get_markov_chain, get_db, prob_list_for_word, all_words_prob

connection, cursor = get_db()
chain = get_markov_chain(cursor)
words = [word.lower() for word in nltk.word_tokenize(sys.argv[1])]

if words[0] not in chain.keys():
    print("Trump has never used the word \"{0}\"".format(words[0]))
    exit(1)
totalProb = float(chain[words[0]]["prob"])
print("BEGINNING PROBABILITY REPORT")
print("WORD                IND          TOTAL")
print("======================================")
print("{0:<20}{1:.3f}%{2:>10.3f}%".format(words[0].upper(), totalProb * 100, totalProb * 100))
for i, word in enumerate(words):
    if i == 0:
        continue
    if words[i] not in chain[words[i-1]]["dst"].keys():
        print("\nAborting, trump has never used the word \"{0}\" after the word \"{1}\"".format(words[i], words[i-1]))
        exit(1)
    prob = chain[words[i-1]]["dst"][words[i]]["prob"]
    totalProb = prob * totalProb
    print("{0:<20}{1:.3f}%{2:>10.4f}%".format(words[i].upper(), prob * 100, totalProb * 100))

next_word_list = prob_list_for_word(chain[words[-1]])
print("\nNEXT MOST LIKELY WORD: \"{0}\"".format(next_word_list[0]["word"].upper()))
