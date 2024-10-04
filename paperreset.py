#!/usr/bin/env python
from logginghelper import logging

from harrytools import config
config = config()
logging.info("Reseting paper position")
config.set("state", "x_pos", config.get("plotter", "start_x_pos"))
config.set("state", "y_pos", config.get("plotter", "start_y_pos"))
config.save()
