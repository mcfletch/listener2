"""DBus API for running an Interpreter for language calls

Provides a mechanism by which code running as the current user 
(namely the listener service) can send messages.

    context setup (i.e. create new language models)
    
        add projects to context 
        
        create new contexts
        
        modify/edit dictionaries
        
        correction process
        
    context choice (switch current context)
    
    sample/training playback
    
    microphone selection enabling/disabling, etc
    
    uinput (keyboard simulation)

We will want to use permission restrictions such that only console 
users can access the uinput service. (There's a sample conf started
for that).

Will (eventually) want the pipelines to run in the Listener service 
and the uinput service to run in a separate service.
    
The code in this module is BSD licensed (as is the rest of listener).

Note: this module loads python-dbus, which on PyPI and in it's source 
distribution declares itself to be MIT licensed, but the FAQ for which 
declares to be a dual license AFL/GPL license.
"""
from __future__ import absolute_import
import gi

gi.require_version('IBus', '1.0')
from gi.repository import IBus
from gi.repository import GObject, GLib, Gio
import dbus
import dbus.service

IBus.init()
from . import eventreceiver, interpreter
import json, logging, threading, time, errno, socket, select, os

log = logging.getLogger(__name__)


def exposed_dbus_prop(name):
    """Exposed a property on DBus and cache locally"""
    local_key = '__%s' % (name,)

    def _getter(self, name):
        return self.__dict__[local_key]

    def _setter(self, name, value):
        self.__dict__[local_key] = value
        self.props_iface.Set(
            self.DBUS_NAME, 'current_context_name', value,
        )
        return value

    _getter.__name__ = name
    _setter.__name__ = name
    return property(
        name=name,
        fget=_getter,
        fset=_setter,
        doc='''Set the value locally and expose as a DBus Property''',
    )


RULE_TYPE = 'a(as,s)'


class InterpreterService(dbus.service.Object):
    """API for interpreting utterances"""

    DBUS_NAME = 'com.vrplumber.listener.interpreter'
    DBUS_PATH = '/com/vrplumber/listener/interpreter'

    def __init__(self, listener, name):
        """Create the interpreter by loading from a directory"""
        self.listener = listener
        self.name = name

    @dbus.service.method(DBUS_NAME, in_signature='', out_signature=RULE_TYPE)
    def load_rules(self):
        """Load/reload the rules for the interpreter"""
        self.rules, self.rule_set = interpreter.load_rules(self.rule_file,)
        return [(rule.match, rule.replace) for rule in self.rule_set]

    @dbus.service.method(DBUS_NAME, in_signature=RULE_TYPE, out_signature='')
    def replace_rules(self):
        """Replace the interpreter's rules with a new set from the rule editor"""

    @dbus.service.method(DBUS_NAME, in_signature='', out_signature='')
    def load_language_models(self):
        """Get the language models for the interpreter"""

    def partial_event(self, event):
        self.listener.partial_event(event)

    def final_event(self, event):
        self.listener.final_event(event)

    def handle_event(self, event):
        """Given an event from the listener, attempt to interpret it"""


class ListenerService(dbus.service.Object):
    """External api to the recognition service """

    DBUS_NAME = 'com.vrplumber.listener'
    DBUS_PATH = '/com/vrplumber/listener'

    def __init__(self):
        bus = dbus.SessionBus()
        bus_name = dbus.service.BusName(self.DBUS_NAME, bus=bus)
        dbus.service.Object.__init__(self, bus_name, self.DBUS_PATH)
        self.contexts = {}
        self.props_iface = bus.get_object('org.freedesktop.DBus.Properties')
        self.current_context_name = 'default'
        self.set_context(self.current_context_name)

    current_context_name = exposed_dbus_prop('current_context_name')
    current_context = exposed_dbus_prop('current_context')

    @dbus.service.method(DBUS_NAME, in_signature='s', out_signature='o')
    def set_context(self, name):
        """Set the context for the DBUS for interpreting incoming events"""
        current = self.contexts.get(name)
        if name is None:
            self.contexts[name] = current = InterpreterService(self, name)
        self.current_context = current
        return current

    @dbus.service.method(DBUS_NAME, in_signature='s', out_signature='o')
    def get_context(self):
        """Get the  current  context for interpretation"""
        return self.current_context

    # @dbus.service.method(DBUS_NAME,)
    # def contexts(self):
    #     """Lists the contexts currently defined in the service

    #     Returns the bus-names of the sub-contexts that can be used
    #     to instantiate them, currently you *must* call this method
    #     """
    #     from . import context

    #     return context.Context.keys()

    @dbus.service.signal('%s.PartialResult' % (DBUS_NAME,), signature='as')
    def partial_event(self, interpreted, text, uttid):
        return interpreted

    @dbus.service.signal('%s.FinalResult' % (DBUS_NAME,), signature='as')
    def final_event(self, interpreted, text, uttid):
        return interpreted

    def input_thread(self):
        """Background thread which processes input and generates events"""
        from . import eventreceiver

        for event in eventreceiver.read_from_socket(
            sockname=EVENTS, connect_backoff=2.0,
        ):
            if event.get('final'):
                for transcript in event['transcripts']:
                    new_words = apply_rules(transcript['words'], rules)
                    transcript['text'] = words_to_text(new_words)
                    transcript['words'] = new_words
                    break
                queue.put(event)


class PipelineService(dbus.service.Object):
    # current pipeline manipulation...
    DBUS_NAME = 'com.vrplumber.listener.pipeline'
    DBUS_PATH = '/com/vrplumber/listener/pipeline'

    def __init__(self, pipeline):
        self.target = pipeline
        bus_name = dbus.service.BusName(self.DBUS_NAME, bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, self.DBUS_PATH)

    @dbus.service.method(DBUS_NAME)
    def start(self):
        """Start up pipeline for current context"""
        return self.target.pipeline.start_listening()

    @dbus.service.method(DBUS_NAME)
    def stop(self):
        """Shut down pipeline for current context"""
        return self.target.pipeline.stop_listening()

    @dbus.service.method(DBUS_NAME)
    def pause(self):
        """Pause listening (block pipeline)"""
        return self.target.pipeline.pause_listening()

    @dbus.service.method(DBUS_NAME)
    def reset(self):
        """Reset/restart the pipeline"""
        return self.target.pipeline.reset()


class ContextService(dbus.service.Object):
    """Service controlling a particular listener context"""

    # Note: this seems to be "interface name", and apparently
    # needs to be different for each class?
    DBUS_NAME = 'com.vrplumber.listener.context'
    DBUS_PATH = '/com/vrplumber/listener/context'

    def __init__(self, target):
        self.target = target
        self.key = target.context.key
        bus_name = dbus.service.BusName(self.DBUS_NAME, bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, self.DBUS_PATH)

    @property
    def context(self):
        return self.target.context

    @dbus.service.method(DBUS_NAME,)
    def delete(self):
        return self.context.delete()

    @dbus.service.method(
        DBUS_NAME, in_signature='s',
    )
    def integrate_project(self, path):
        """Import a project from the given path"""
        return self.context.integrate_project(path)


def main():
    mainloop = MAINLOOP = GLib.MainLoop()
    bus = BUS = IBus.Bus()

    def on_disconnected(bus):
        mainloop.quit()

    bus.connect('disconnected', on_disconnected)

    # TODO: we should be checking the result here, the sync method just times out
    # but the async one seems to work, just takes a while
    log.debug("Starting mainloop")
    mainloop.run()
