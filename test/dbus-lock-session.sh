#!/bin/bash

set -e


sleep 1


##
## lock screen
##
dbus-send --session --dest=org.freedesktop.ScreenSaver --type=method_call --print-reply /ScreenSaver org.freedesktop.ScreenSaver.Lock
