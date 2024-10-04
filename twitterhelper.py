__author__ = "p91 <p91.hasi.it>"
__version__ = 0.1
__date__ = "22.10.2012"
__status__ = "testing"

from logginghelper import logging
import time

try:
	import twitter
	if not twitter.__author__ == 'python-twitter@googlegroups.com':
		raise AttributeError
except AttributeError, e:
	logging.exception("Wrong twitter module used! Please use this one: https://code.google.com/p/python-twitter/")
	logging.exception(e)
	exit()
except ImportError, e:
	logging.exception("Twitter module not found! Please download this one: https://code.google.com/p/python-twitter/")
	logging.exception(e)
	exit()

class TweetsError(Exception):
	def __init__(self, e):
		self.e = e
	def __str__(self):
		return self.e.__str__()

class Tweet:
	def __init__(self, screen_name, id, text):
		self.user = self.User(screen_name)
		self.id = id
		self.text = text

	class User:
		def __init__(self, screen_name):
			self.screen_name = screen_name

def get_tweets_by_terms(terms, last_id, refresh_time = 10, tweets_per_page = 100, recursive = True):
	tweet_list = []
	id_list = []
	for term in terms:
		try:
			tweets = get_tweets_by_term(term, last_id, refresh_time, tweets_per_page, recursive)
		except Exception, e :
			raise TweetsError(e)
		#check for double tweets
		for tweet in tweets:
			if not tweet.id in id_list:
				tweet_list.append(tweet)
				id_list.append(tweet.id)
	tweet_list.sort(key = lambda x: x.id, reverse=False)
	return tweet_list

#from here on dependend on the avaiable twitter api

def get_tweets_by_term(term, last_id, refresh_time = 10, tweets_per_page = 100, recursive = True):
	tweets = []
	while True:
		time.sleep(refresh_time)
		tmptweets = twitter.Api().GetSearch(term=term, since_id=last_id, per_page=tweets_per_page, lang=None)
		tweets.extend([Tweet(i.user.screen_name, i.id, i.text) for i in tmptweets])
		if not (len(tmptweets) == tweets_per_page and recursive):
			break
		last_id = tweets[-1].id
	return tweets
