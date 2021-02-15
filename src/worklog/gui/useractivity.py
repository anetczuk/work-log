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

import logging

from PyQt5.QtCore import QObject, pyqtSignal

from worklog.dbus.useractivitydetector import ScreenSaverDetector
# from worklog.dbus.useractivitydetector import SessionDetector


_LOGGER = logging.getLogger(__name__)


class UserActivity( QObject ):

    ### state:
    ###    True  -- screen saver started
    ###    False -- screen saver stopped
    ssaverChanged  = pyqtSignal( bool )
    ### state:
    ###    True  -- session locked
    ###    False -- session unlocked
    sessionChanged = pyqtSignal( bool )

    def __init__(self, parentWidget=None):
        super().__init__( parentWidget )

        self.screenSaverDetector = ScreenSaverDetector()
        self.screenSaverDetector.setCallback( self._screenSaverActivationCallback )

        ## disable session detector -- causes problems under KDE on suspend (lid close)
#         self.sessionDetector = SessionDetector()
#         self.sessionDetector.setCallback( self._sessionActivityCallback )

    def isAwayFromKeyboard(self):
        if self.screenSaverDetector.isActivated():
            _LOGGER.info( "screen saver active" )
            return True
#         if self.sessionDetector.isLocked():
#             _LOGGER.info( "session locked" )
#             return True
        return False

    def _screenSaverActivationCallback(self, activated):
        if activated != 0:
            _LOGGER.info( "screen saver started" )
            self.ssaverChanged.emit( True )
        else:
            _LOGGER.info( "screen saver stopped" )
            self.ssaverChanged.emit( False )

    def _sessionActivityCallback(self, activated):
        if activated != 0:
            _LOGGER.info( "session locked" )
            self.sessionChanged.emit( True )
        else:
            _LOGGER.info( "session unlocked" )
            self.sessionChanged.emit( False )
