from markov import get_db
from collections import Counter
import nltk
import pandas as pd
import re as regex
import numpy as np
import plotly
from sklearn.metrics import f1_score, precision_score, recall_score, accuracy_score
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV, RandomizedSearchCV
from time import time
import gensim

connection, cursor = get_db()
cursor.execute("SELECT * FROM base_tweets WHERE (source = 'Twitter for iPhone' OR source = 'Twitter for Android')"
               "AND is_retweet = 0 AND YEAR(created) >= 2015")
tweets = [str(x[0]) for x in cursor.fetchall()]
