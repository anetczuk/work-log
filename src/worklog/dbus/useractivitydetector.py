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

import os
import logging
import dbus
# import threading
# from gi.repository import GObject


_LOGGER = logging.getLogger(__name__)


class ScreenSaverDetector():

    def __init__(self, dbus_loop=None):
        self.bus = None
        self.saver_interface = None
        self.dbus_interface = None
        self.enabledCallback = True
        self.saverStateCallback = None

        ## find interface
        if dbus_loop is not None:
            self.bus = dbus.SessionBus( mainloop=dbus_loop )
        else:
            self.bus = dbus.SessionBus()
        
        interfaces = ('org.freedesktop.ScreenSaver', 'org.kde.screensaver', 'org.gnome.ScreenSaver')
        for iface in interfaces:
            try:
                saver = self.bus.get_object(iface, '/ScreenSaver')
                ## _LOGGER.debug("Using object: %s", iface)
                self.saver_interface = dbus.Interface(saver, dbus_interface=iface)
                ## print("methods:\n", saver.Introspect())

                ## register signal receiver
                self.bus.add_signal_receiver( self._screenSaverChangedCallback,
                                              'ActiveChanged',
                                              iface,
                                              path='/ScreenSaver' )
                self.dbus_interface = iface
                _LOGGER.debug( "screensaver interface detected: %s", iface )
                break
            except dbus.exceptions.DBusException:
                ## do nothing
                pass
        if self.saver_interface is None:
            _LOGGER.warning("could not detect screensaver interface")

    def __del__(self):
        ## body of destructor
        self.unregister()
        self.saver_interface = None

    def isActivated(self):
        if self.saver_interface is None:
            return 0
        try:
            return self.saver_interface.GetActive()
        except dbus.exceptions.DBusException:
            ## unable to get information about screen saver -- assume not activated
            return 0

    def setEnabled(self, new_state=True):
        self.enabledCallback = new_state

    def setCallback(self, callback):
        """
        Register callback on user activity.

        Callback receives one parameter: bool
        """
        self.saverStateCallback = callback

    def unregister(self):
        if self.saver_interface is None:
            return
        ## clean up by removing the signal handler
        self.bus.remove_signal_receiver(  self._screenSaverChangedCallback,
                                          'ActiveChanged',
                                          self.dbus_interface,
                                          path='/ScreenSaver' )

    ## newState values:
    ##      1 -- screensaver activated
    ##      0 -- screensaver deactivated
    def _screenSaverChangedCallback(self, newState):
        _LOGGER.debug( "screensaver activation changed: %s", newState )
        if self.enabledCallback is False:
            return
        if self.saverStateCallback is None:
            return
        self.saverStateCallback( newState )


##
## it seems that under KDE the signals aren't received
##
class SessionDetector():

    def __init__(self, dbus_loop=None):
        self.bus = None
        self.saver_interface = None
        self.dbus_interface = None

        self.lockState = 0
        self.enabledCallback = True
        self.activityCallback = None

        ## find interface
        if dbus_loop is not None:
            self.bus = dbus.SystemBus( mainloop=dbus_loop )
        else:
            self.bus = dbus.SystemBus()

        managerIface = self._getInterface('/org/freedesktop/login1', 'org.freedesktop.login1.Manager')

        pid = os.getpid()
        currSessionPath = managerIface.GetSessionByPID( pid )
        self.currentSession = self._getObject( currSessionPath )
        self.currentSessionProps = dbus.Interface(self.currentSession, 'org.freedesktop.DBus.Properties')

        currentSeatPath = self.currentSessionProps.Get( 'org.freedesktop.login1.Session', 'Seat')[1]
        self.currentSeat = self._getObject( currentSeatPath )
        self.currentSeatProps = dbus.Interface(self.currentSeat, 'org.freedesktop.DBus.Properties')

        ## _LOGGER.debug( "seat: {0} t:{1}".format( self.currentSeat, type(self.currentSeat) ) )

        self.currentSession.connect_to_signal( "PropertiesChanged", self._sessionPropertiesChangedCallback,
                                               'org.freedesktop.DBus.Properties' )
        self.currentSession.connect_to_signal( "Lock", self._sessionLockCallback, 'org.freedesktop.login1.Session' )
        self.currentSession.connect_to_signal( "Unlock", self._sessionUnlockCallback,
                                               'org.freedesktop.login1.Session' )

    def setCallback(self, callback):
        """
        Register callback on user session state change.

        Callback receives one parameter: bool
        """
        self.activityCallback = callback
        
    def isLocked(self):
        if self.lockState != 0:
            return True
        return False

    def _sessionLockCallback(self):
        _LOGGER.debug( "session locked" )
        self._stateChanged( 1 )

    def _sessionUnlockCallback(self):
        _LOGGER.debug( "session unlocked" )
        self._stateChanged( 0 )

    def _sessionPropertiesChangedCallback(self, *args):
        _LOGGER.debug( "session props change: %s", args )

        ##activeSession = self.currentSeatProps.Get( 'org.freedesktop.login1.Seat', 'ActiveSession')[0]
        ##sessionState = self.currentSessionProps.Get( 'org.freedesktop.login1.Session', 'State')
        ##_LOGGER.debug( "active session: {0} curr session state: {1}".format( activeSession, sessionState ) )

        propDict = args[1]
        activeValue = propDict["Active"]
        if activeValue is None:
            return
        if activeValue is True:
            self._stateChanged( False )
        else:
            self._stateChanged( True )

    def _stateChanged(self, newState):
        self.lockState = newState
        if self.enabledCallback is False:
            return
        if self.activityCallback is None:
            return
        self.activityCallback( newState )

    def _getPropertiesInterface(self, object_path):
        return self._getInterface(object_path, 'org.freedesktop.DBus.Properties')

    def _getInterface(self, object_path, interface_name):
        busObject = self._getObject( object_path )
        return dbus.Interface(busObject, interface_name)

    def _getObject(self, object_path):
        return self.bus.get_object('org.freedesktop.login1', object_path)


# class DBusThread( threading.Thread ):
#
#     def __init__(self):
#         super().__init__()
#
#     def run(self):
#         _LOGGER.info("starting dbus main loop")
#         GObject.MainLoop().run()
