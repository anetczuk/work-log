#!/usr/bin/python3
#
# MIT License
#
# Copyright (c) 2020 Arkadiusz Netczuk <dev.arnet@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

try:
    ## following import success only when file is directly executed from command line
    ## otherwise will throw exception when executing as parameter for "python -m"
    # pylint: disable=W0611
    import __init__ as package_init
except ImportError:
    ## when import fails then it means that the script was executed indirectly
    ## in this case __init__ is already loaded
    pass

import logging

from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GObject

import worklog.logger as logger
from worklog.dbus.useractivitydetector import ScreenSaverDetector, SessionDetector


logFile = logger.get_logging_output_file()
logger.configure( logFile )

_LOGGER = logging.getLogger(__name__)


class UserActivity():

    def __init__(self):
        self.screenSaverDetector = ScreenSaverDetector()
        self.screenSaverDetector.setCallback( self._screenSaverActivationCallback )

        self.sessionDetector = SessionDetector()
        self.sessionDetector.setCallback( self._sessionActivityCallback )

    def _screenSaverActivationCallback(self, activated):
        _LOGGER.info( "screen saver active: %s", activated )

    def _sessionActivityCallback(self, activated):
        _LOGGER.info( "session active: %s", activated )


if __name__ == '__main__':
    #from .main import main

    _LOGGER.debug( "Logger log file: %s", logger.log_file )

    DBusGMainLoop(set_as_default=True)

    activity = UserActivity()

    # Start the loop and wait for the signal
    GObject.MainLoop().run()
