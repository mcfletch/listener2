"""Debug dbus events on the console"""
import logging
from .hostgi import gi
from gi.repository import GLib

import dbus
import dbus.mainloop.glib
from . import defaults

log = logging.getLogger(__name__)


def on_event(*args, **named):
    print("Event:", args)


def main():

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    dbus_bus = dbus.SessionBus()
    # bus_name = dbus.BusName(defaults.DBUS_NAME, bus=self.dbus_bus)
    # self.dbus_bus.connect()

    remote_object = dbus_bus.get_object(
        defaults.DBUS_NAME, defaults.DBUS_INTERPRETER_PATH,
    )
    iface = dbus.Interface(remote_object, defaults.DBUS_NAME)
    log.info("Interface: %s", iface)
    dbus_bus.add_signal_receiver(
        on_event,
        dbus_interface=defaults.PARTIAL_RESULT_EVENT,
        # path='/Listener',
        # signal_name=defaults.FINAL_RESULT_EVENT.split('.')[-1],
        # utf8_strings=True,
    )

    mainloop = GLib.MainLoop()
    mainloop.run()
