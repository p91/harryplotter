#!/bin/bash
start-stop-daemon --stop --chdir /harryplotter --pidfile harryplotter.pid
./paperreset.py
start-stop-daemon --start --background  \
--chdir /harryplotter \
--make-pidfile --pidfile harryplotter.pid \
--exec /usr/bin/python harryplotter.py
exit 0

