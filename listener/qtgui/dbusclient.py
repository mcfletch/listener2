"""DBus thread for RPC to Listener Service from Qt/Pyside2 GUI"""
from __future__ import absolute_import
from .hostgi import gi

from gi.repository import GObject, GLib, Gio
import dbus
import dbus.service

IBus.init()
from . import eventreceiver, interpreter
import json, logging, threading, time, errno, socket, select, os


def start_dbus():
    """Start running a DBus mainloop with queues for bi-directional messages and events"""
