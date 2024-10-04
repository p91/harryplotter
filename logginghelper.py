import sys
import time

try:
	import logging
	import logging.handlers
	import logging.config
	if not logging.__author__ == 'Vinay Sajip <vinay_sajip@red-dove.com>':
		raise AttributeError
except AttributeError, e:
	print >> sys.stderr, 'Apparently wrong logging module installed'
	exit()
except ImportError:
	print >> sys.stderr, 'logging modul not found!'
	exit()

class alreadySent(logging.Filter):
	def __init__(self):
		self.lastErrorTime = 0
		self.lastErrorMessage = ""
		self.ErrorInterval = 3600 #1 hour 

	def filter(self, rec):
		if rec.message == self.lastErrorMessage:
			if rec.created >= self.lastErrorTime + self.ErrorInterval:
				self.lastErrorTime = rec.created
				return True
			else:
				return False
		else:
			self.lastErrorMessage = rec.message
			self.lastErrorTime = rec.created
			return True

class SMTPHandlerlimited(logging.handlers.SMTPHandler):
	def __init__(self, *args, **kwargs):
		logging.handlers.SMTPHandler.__init__(self, *args, **kwargs)
		self.addFilter(alreadySent())

logging.config.fileConfig("config.cfg")

tweetlog = logging.getLogger('tweetlogger')
hpgllog = logging.getLogger("hpgllogger") 

def tweet(tweetobject):
	tweetlog.info(tweetobject.text.replace("\n", ""), extra={'username': tweetobject.user.screen_name, 'id': tweetobject.id})

def hpgl(text):
	hpgllog.info(text)


logging.tweet = tweet
logging.hpgl = hpgl
