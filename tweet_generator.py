#!/usr/bin/python
from markov import get_markov_chain, get_db, prob_list_for_word
from sacremoses import MosesDetokenizer
import random





connection, cursor = get_db()
chain = get_markov_chain(cursor)
detokenizer = MosesDetokenizer()
for i in range(0, 10):
    sentence = [get_next_word(chain, "START")]
    while True:
        next_word = get_next_word(chain, sentence[-1])
        if next_word == "END":
            break
        sentence.append(next_word)
    compiled_sentence = detokenizer.detokenize(sentence)
    print(str(i) + ": " + compiled_sentence)
