#!/bin/bash

start-stop-daemon --start --background \
--make-pidfile --pidfile harryplotter.pid \
--chdir /harryplotter \
--exec /usr/bin/python harryplotter.py

exit 0
