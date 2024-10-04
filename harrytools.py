__author__ = "p91 <p91.hasi.it>"
__version__ = 0.4
__date__ = "10.12.2012"
__status__ = "testing"

from logginghelper import logging
from collections import deque
import ConfigParser
import time
import serial

class PlotterError(Exception):
	def __init__(self, e):
		self.e = e
	def __str__(self):
		return self.e.__str__()

class config:
	#config class which implements a seperation between state and config
	#all writes go to state, reading has priority on state and config as fallback
	def __init__(self):
		self.config = ConfigParser.SafeConfigParser()
		self.config.read('config.cfg')
		self.state = ConfigParser.SafeConfigParser()
		self.state.read(self.config.get("main", "statefile"))
		#populate state
		if self.config.getboolean("state", "use_last_id_from_config") or not self.state.has_option("state", "last_id"):
			try:
				self.state.set("state", "last_id", str(self.config.getint("twitter", "start_last_id")))
			except ConfigParser.NoSectionError:
				self.state.add_section("state")
				self.state.set("state", "last_id", str(self.config.getint("twitter", "start_last_id")))
		if (self.config.getboolean("state", "use_xy_pos_from_config") or \
		not (self.state.has_option("state", "x_pos") and self.state.has_option("state", "y_pos"))):
			try:
				self.state.set("state", "x_pos", str(self.config.getint("plotter", "start_x_pos")))
				self.state.set("state", "y_pos", str(self.config.getint("plotter", "start_y_pos")))
			except ConfigParser.NoSectionError:
				self.state.add_section("state")
				self.state.set("state", "x_pos", str(config.getint("plotter", "start_x_pos")))
				self.state.set("state", "y_pos", str(config.getint("plotter", "start_y_pos")))
		self.save()

	def save(self):
		with open(self.config.get("main", "statefile"),'w') as statefile:
			self.state.write(statefile)

	def add_section(self, section):
		self.state.add_section(section)
		self.save()

	def has_section(self, section):
		return self.config.has_section(section) or self.state.has_section(section) 

	def has_option(self, section, option):
		return self.config.has_option(section, option) or self.state.has_option(section, option)
 
	def set(self, section, option, value=None):
		self.state.set(section, option, value)

	def get(self, section, option):
		try:
			return self.state.get(section, option)
		except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
			return self.config.get(section, option)

	def getint(self, section, option):
		try:
			return self.state.getint(section, option)
		except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
			return self.config.getint(section, option)

	def getfloat(self, section, option):
		try:
			return self.state.getfloat(section, option)
		except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
			return self.config.getfloat(section, option)

	def getboolean(self, section, option):
		try:
			return self.state.getboolean(section, option)
		except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
			return self.config.getboolean(section, option)

class plotter:
	def __init__(self, config):
		self.config = config
		self.__serial_device = config.get("plotter", "serial_device")
		self.__baudrate = config.getint("plotter", "baudrate")
		self.__x_pos = config.getint("state", "x_pos")
		self.__y_pos = config.getint("state","y_pos")
		self.__tweet_process_time = config.getint("plotter", "tweet_process_time")
		self.__last_print_time = time.time()
		self.__termiantor_symbol = chr(config.getint("plotter", "termiantor_symbol_ascii_code"))
		self.__tweet_row_distance = config.getint("plotter", "tweet_row_distance")
		self.__chars_per_line = config.getint("plotter", "chars_per_line")
		self.__pre_username = config.get("plotter", "pre_username")
		self.__post_username = config.get("plotter","post_username")
		self.__username_tweet_seperator = self.config.get("plotter", "username_tweet_seperator")
		self.__max_username_size = config.getint("twitter", "max_username_size")
		self.DEBUG = False
		try:
			self.__serial = serial.Serial(port = self.__serial_device, baudrate=self.__baudrate)
			self.__serial.open()
		except Exception, e:
			logging.error("Serial device could not be opened. The plotter class will enable DEBUG-Mode meaning all writing to the serial interface is disabled and will raise an PlotterError if it is tried")


	def __del__(self):
		if not self.DEBUG:
			try:
				self.__serial.close()
			except Exception, e:
				logging.error("Serial device could not be closed")
				raise PlotterError(e)

	def __send(self, text):
		if self.DEBUG:
			raise PlotterError("Writing to Plotter in Debug Mode")
		logging.hpgl(text)
		try:
			while (time.time() <= self.__tweet_process_time + self.__last_print_time) or not self.__serial.isOpen():
				#wait time between tweets or if serial port is not yet ready
				time.sleep(1)
			self.__serial.write(text)
			self.__serial.flush()
		except Exception, e:
			logging.error("Could not write to serial device")
			raise PlotterError(e)

	def generate_lines(self, tweet):
		#generate a list of lines, all smaller then the max line size and with user name + intend in front
		user = "".join([self.__pre_username, tweet.user.screen_name, self.__post_username])
		user = user.ljust(self.__max_username_size + len(self.__pre_username) + len(self.__post_username)) 
		intend = " " * len(user) + self.__username_tweet_seperator
		lines = []
		line = user + self.__username_tweet_seperator
		wordlist = deque(tweet.text.split())
		maxlinelength = self.__chars_per_line
		maxtweetline = maxlinelength - len(intend)
		while len(wordlist) > 0:
			word = wordlist.popleft()
			if len(word) > maxtweetline:
				#split words which are too long for one line
				wordlist.appendleft(word[maxtweetline:])
				word = word[:maxtweetline]
			if len(line + word) > maxlinelength:
				#word does not fit line anymore
				lines.append(line.rstrip())
				line = intend + word
			else:
				#word still fits the line
				line += word
			if len(wordlist) == 0:
				lines.append(line)
			line += " "
		return lines

	def plot_tweet(self, tweet):
		lines = self.generate_lines(tweet)
		tweet_plotter_code = self.generate_hpgl(lines, self.__x_pos, self.__y_pos)
		self.__send(tweet_plotter_code)
		y_diff = self.__tweet_row_distance * (len(lines))
		self.__y_pos += y_diff
		self.config.set("state", "x_pos", str(self.__x_pos))
		self.config.set("state", "y_pos", str(self.__y_pos))
		self.config.set("state", "last_id", str(tweet.id))
		self.config.save()
		return True

	def generate_hpgl(self, lines, x, y):
		linenumber = len(lines)
		stringlist = ["IN;DT", self.__termiantor_symbol, ",1;DI0,-1;SI0.18,0.18;PU", \
		str(y + linenumber * self.__tweet_row_distance), ",", str(x), ";LB"]
		stringlist.extend((chr(10) + chr(13)).join([line.encode("ascii", "replace") for line in lines]))
		stringlist.append(self.__termiantor_symbol)
		stringlist.append(";")
		return "".join(stringlist)
