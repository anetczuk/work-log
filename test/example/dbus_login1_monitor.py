#!/usr/bin/env python


from datetime import datetime
import dbus
from gi.repository import GObject
from dbus.mainloop.glib import DBusGMainLoop


DBusGMainLoop(set_as_default=True)


def listnames_example():
    bus = dbus.SessionBus()
     
    # Create an object that will proxy for a particular remote object.
    remote_object = bus.get_object(
        "org.freedesktop.DBus", # Bus name
        "/org/freedesktop/DBus" # Object path
    )
     
    # Introspection returns an XML document containing information
    # about the methods supported by an interface.
    print( "Introspection data:\n" )
    print( remote_object.Introspect() )   
#     print( remote_object.ListNames() )
  
# listnames_example()


def properties_changed_callback(*args):
    print( "%s login1: %s" % (datetime.now().ctime(), args) )
    propDict = args[1]
    print ("dict: %s" % type(propDict) )
    print( "active: %s" % propDict["Active"] )

dbus.SystemBus().add_signal_receiver(
    properties_changed_callback,
    signal_name='PropertiesChanged',
    dbus_interface='org.freedesktop.DBus.Properties',
    bus_name='org.freedesktop.login1'
)


def screensaver_changed_callback(*args):
    print( "%s: screen saver: %s" % (datetime.now().ctime(), args) )

dbus.SessionBus().add_signal_receiver(
    screensaver_changed_callback,
    signal_name=None,
    dbus_interface='org.freedesktop.ScreenSaver'
#     bus_name='org.freedesktop.ScreenSaver'
)


GObject.MainLoop().run()

