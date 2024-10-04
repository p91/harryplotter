#!/usr/bin/env python
def update_last_id(config):
	tweets = None
	logging.debug("updating last id on start")
	while tweets is None:
		try:
			tweets = get_tweets_by_terms(terms, config.getint("state", "last_id"), tweets_per_page = config.getint("twitter", "tweets_per_page"), recursive = False)
		except TweetsError, e:
			logging.info("A TweetsError accured.")
			logging.info(e)
		except Exception, e:
			logging.exception(e)
	config.set("state", "last_id", str(tweets[-1].id) if len(tweets) is not 0 else config.get("state", "last_id"))

def processing_loop(config, terms):
	tweets = None
	logging.info("Searching twitter")
	while tweets is None:
		try:
			tweets = get_tweets_by_terms(terms, config.getint("state", "last_id"), \
			tweets_per_page = config.getint("twitter", "tweets_per_page"), recursive = True)
		except TweetsError, e:
			logging.info("A TweetsError accured.")
			logging.info(e)
		except Exception, e:
			logging.exception(e)
	logging.debug(str(len(tweets)) + " tweets found")
	try:
		for tweet in tweets:
			while not harry.plot_tweet(tweet): time.sleep(1)
			logging.debug("Plotted tweet: " + str(tweet.id))
			logging.tweet(tweet)
		logging.debug("Tweets plotted")
	except PlotterError, e:
		logging.exception(e)

import atexit
from logginghelper import logging
from harrytools import plotter, config, PlotterError
from twitterhelper import get_tweets_by_terms, TweetsError

config = config()
harry = plotter(config)

def cleanup():
	config.save()
	logging.info("Programm was closed")
	logging.shutdown()

def main():
	terms = [term.strip() for term in config.get("twitter", "terms").split(",")]
	logging.info("Programm  started")
	logging.debug("Serial Interface: " + config.get("plotter", "serial_device"))
	logging.debug("Twitter Terms: " + config.get("twitter", "terms"))
	if config.getboolean("twitter", "update_last_id_on_start"):
		update_last_id(config)

	while True:
		try:
			processing_loop(config, terms)
		except KeyboardInterrupt:
			break
		except Exception, e:
			logging.exception(e)

if __name__ == '__main__':
	atexit.register(cleanup)
	main()

