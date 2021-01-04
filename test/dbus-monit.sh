#!/bin/bash

set -e


##
## ts  -- add timestamp to each output line
## tee -- redirects output to stdout and to file
##

dbus-monitor  | ts '[%Y-%m-%d %H:%M:%.S]' | tee /tmp/dbus_monit.txt
