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
    import __init__
except ImportError:
    ## when import fails then it means that the script was executed indirectly
    ## in this case __init__ is already loaded
    pass

import sys
import logging
import argparse
from datetime import date, time

from dbus.mainloop.glib import DBusGMainLoop

# from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication

import worklog.logger as logger
from worklog.gui.sigint import setup_interrupt_handling
from worklog.gui.mainwindow import MainWindow
# from worklog.gui.resources import get_root_path
# from worklog.gui.utils import render_to_pixmap


## ============================= main section ===================================


if __name__ != '__main__':
    sys.exit(0)


parser = argparse.ArgumentParser(description='Work Log Example')
parser.add_argument('-lud', '--loadUserData', action='store_const', const=True, default=False, help='Load user data' )
parser.add_argument('--minimized', action='store_const', const=True, default=False, help='Start minimized' )

args = parser.parse_args()


logFile = logger.get_logging_output_file()
logger.configure( logFile )

_LOGGER = logging.getLogger(__name__)


_LOGGER.debug( "Starting the application" )


## start dbus loop
DBusGMainLoop(set_as_default=True)

app = QApplication(sys.argv)
app.setApplicationName("WorkLog")
app.setOrganizationName("arnet")
app.setQuitOnLastWindowClosed( False )

setup_interrupt_handling()

window = MainWindow()
window.loadSettings()

window.data.history.addEntryTime( date(year=2020, month=3, day=18),
                                  time(hour=9, minute=15), time(hour=12, minute=0), "Task 1" )
window.data.history.addEntryTime( date(year=2020, month=3, day=22),
                                  time(hour=8, minute=0), time(hour=15, minute=0), "Task 2" )
window.data.history.addEntryTime( date(year=2020, month=3, day=22),
                                  time(hour=18, minute=0), time(hour=20, minute=0), "Task 3", False )

window.setWindowTitleSuffix( "Preview" )
window.disableSaving()
window.setWindowTitle( window.windowTitle() )
if args.loadUserData:
    window.loadData()
else:
    window.readFromKernlog()
    window.ui.navcalendar.setSelectedDate( window.data.history[-1].startTime )

if args.minimized is True or window.appSettings.startMinimized is True:
    ## starting minimized
    pass
else:
    window.show()

# def make_screen():
#     _LOGGER.info("making screenshot")
#     root_path = get_root_path()
#     render_to_pixmap( window, root_path + "/tmp/mainwindow-big.png" )
#
#
# QtCore.QTimer.singleShot(3000, make_screen)

exitCode = app.exec_()

if exitCode == 0:
    window.saveSettings()

sys.exit( exitCode )
