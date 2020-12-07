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
import json, logging, threading, time, errno, socket, select, os, queue
from .hostgi import gi

gi.require_version('IBus', '1.0')
from gi.repository import IBus
from gi.repository import GObject, GLib, Gio
import dbus
import dbus.service

IBus.init()
from . import eventreceiver, interpreter, defaults, models, ibusengine

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
        # name=name,
        fget=_getter,
        fset=_setter,
        doc='''Set the value locally and expose as a DBus Property''',
    )


RULE_TYPE = 'a(ass)'


class InterpreterService(dbus.service.Object):
    """API for interpreting utterances"""

    DBUS_NAME = defaults.DBUS_NAME
    DBUS_PATH = defaults.DBUS_INTERPRETER_PATH

    def __init__(self, listener):
        """Create the interpreter by loading from a directory"""
        self.listener = listener
        self.active = True
        bus_name = dbus.service.BusName(self.DBUS_NAME, bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, self.DBUS_PATH)
        self.event_queue = queue.Queue()
        self.interpreter = interpreter.Interpreter(
            current_context_name=self.listener.current_context_name,
        )
        self.interpreter_thread = threading.Thread(
            target=self.interpreter.run, args=(self.event_queue,),
        )
        self.interpreter_thread.setDaemon(True)
        self.interpreter_thread.start()
        self.shovel_thread = threading.Thread(
            target=self.shovel_events, args=(self.event_queue,)
        )
        self.shovel_thread.setDaemon(True)
        self.shovel_thread.start()

    def shovel_events(self, event_queue):
        """Shovel events from event queue into IBus component"""
        while self.active:
            try:
                event = event_queue.get(True, 5)
            except queue.Empty:
                pass
            else:
                self.listener.handle_event(event)

    @dbus.service.method(DBUS_NAME, in_signature='', out_signature=RULE_TYPE)
    def load_rules(self):
        """Load/reload the rules for the interpreter"""
        self.rules, self.rule_set = interpreter.load_rules(self.rule_file,)
        return [(rule.match, rule.replace) for rule in self.rule_set]

    @dbus.service.method(DBUS_NAME, in_signature=RULE_TYPE, out_signature='')
    def replace_rules(self, rules):
        """Replace the interpreter's rules with a new set from the rule editor"""

    @dbus.service.method(DBUS_NAME, in_signature='', out_signature='')
    def load_language_models(self):
        """Get the language models for the interpreter"""


class ListenerService(dbus.service.Object):
    """External api to the recognition service """

    DBUS_NAME = defaults.DBUS_NAME
    DBUS_PATH = defaults.DBUS_SERVICE_PATH

    def __init__(self):
        bus_name = dbus.service.BusName(self.DBUS_NAME, bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, self.DBUS_PATH)
        self.contexts = {}
        self.current_context_name = 'english-python'
        self.SetContext(self.current_context_name)
        self.interpreter = InterpreterService(self)

    @dbus.service.method(
        dbus_interface=dbus.PROPERTIES_IFACE, in_signature='ss', out_signature='v'
    )
    def Get(self, interface_name, property_name):
        """Get a property via introspection api"""
        return self.GetAll(interface_name)[property_name]

    @dbus.service.method(
        dbus_interface=dbus.PROPERTIES_IFACE, in_signature='s', out_signature='v'
    )
    def GetAll(self, interface_name):
        """Set all properties via introspection api"""
        if interface_name == self.DBUS_NAME:
            return {
                'current_context_name': self.current_context_name,
                'current_context': self.current_context,
                'interpreter': self.interpreter,
            }
        else:
            raise dbus.exceptions.DBusException(
                'org.listener.UnknownInterface',
                '%s does not implement the %s interface'
                % (self.__class__.__name__, interface_name),
            )

    @dbus.service.method(
        dbus_interface=dbus.PROPERTIES_IFACE, in_signature='sss', out_signature='v'
    )
    def Set(self, interface_name, property_name, value):
        """Set the property via introspection api"""
        if interface_name == self.DBUS_NAME:
            if property_name == 'current_context_name':
                self.set_context(value)
                return value
            raise dbus.exceptions.DBusException(
                'org.listener.UnknownProperty',
                'Unknown property: %s' % (property_name,),
            )
        else:
            raise dbus.exceptions.DBusException(
                'org.listener.UnknownInterface',
                '%s does not implement the %s interface'
                % (self.__class__.__name__, interface_name),
            )

    @dbus.service.method(DBUS_NAME, in_signature='s', out_signature='o')
    def SetContext(self, name):
        """Set the context for the DBUS for interpreting incoming events"""
        current = self.contexts.get(name)
        if name is None:
            self.contexts[name] = current = InterpreterService(self, name)
        self.current_context = current
        return current

    @dbus.service.method(DBUS_NAME, in_signature='', out_signature='o')
    def GetContext(self):
        """Get the  current  context for interpretation"""
        return self.current_context

    @dbus.service.method(DBUS_NAME, in_signature='', out_signature='as')
    def GetContextNames(self):
        """Get the  current  context for interpretation"""
        from . import models

        return sorted(models.ContextDefinition.context_names())

    # @dbus.service.method(DBUS_NAME,)
    # def contexts(self):
    #     """Lists the contexts currently defined in the service

    #     Returns the bus-names of the sub-contexts that can be used
    #     to instantiate them, currently you *must* call this method
    #     """
    #     from . import context

    #     return context.Context.keys()
    def handle_event(self, event: models.Utterance):
        """Dispatch the event to the appropriate targets"""
        try:
            self._handle_event(event)
        except Exception as err:
            log.error("Unable to process utterance %s: %s", err, event)
            return

    def _handle_event(self, event: models.Utterance):
        """Handle incoming utterance by dispatching signals, text and keystrokes"""
        ibus = self.ibus
        if ibus:
            ibus.on_decoding_event(event)
        else:
            log.debug('No ibus is running locally')
        # import pdb

        # pdb.set_trace()
        if event.partial:
            if event.transcripts:
                self.PartialResult(event.dbus_struct())
        elif event.final:
            if event.transcripts:
                self.FinalResult(event.dbus_struct())

    @property
    def ibus(self):
        """Gets the current ibusengine instance"""
        return ibusengine.ListenerEngine.INSTANCE

    @dbus.service.signal(
        defaults.PARTIAL_RESULT_EVENT,
        signature=models.Utterance.dbus_struct_signature(),
    )
    def PartialResult(self, evt):
        """Signal sent when a partial transcription is received"""
        return evt

    @dbus.service.signal(
        defaults.FINAL_RESULT_EVENT, signature=models.Utterance.dbus_struct_signature(),
    )
    def FinalResult(self, evt):
        """Signal sent when a final transcription is received (including interpretation)"""
        log.debug("Sending final event: %s", evt)
        # return evt


# class PipelineService(dbus.service.Object):
#     # current pipeline manipulation...
#     DBUS_NAME = 'com.vrplumber.listener.pipeline'
#     DBUS_PATH = '/com/vrplumber/listener/pipeline'

#     def __init__(self, pipeline):
#         self.target = pipeline
#         bus_name = dbus.service.BusName(self.DBUS_NAME, bus=dbus.SessionBus())
#         dbus.service.Object.__init__(self, bus_name, self.DBUS_PATH)

#     @dbus.service.method(DBUS_NAME)
#     def start(self):
#         """Start up pipeline for current context"""
#         return self.target.pipeline.start_listening()

#     @dbus.service.method(DBUS_NAME)
#     def stop(self):
#         """Shut down pipeline for current context"""
#         return self.target.pipeline.stop_listening()

#     @dbus.service.method(DBUS_NAME)
#     def pause(self):
#         """Pause listening (block pipeline)"""
#         return self.target.pipeline.pause_listening()

#     @dbus.service.method(DBUS_NAME)
#     def reset(self):
#         """Reset/restart the pipeline"""
#         return self.target.pipeline.reset()


# class ContextService(dbus.service.Object):
#     """Service controlling a particular listener context"""

#     # Note: this seems to be "interface name", and apparently
#     # needs to be different for each class?
#     DBUS_NAME = 'com.vrplumber.listener.context'
#     DBUS_PATH = '/com/vrplumber/listener/context'

#     def __init__(self, target):
#         self.target = target
#         self.key = target.context.key
#         bus_name = dbus.service.BusName(self.DBUS_NAME, bus=dbus.SessionBus())
#         dbus.service.Object.__init__(self, bus_name, self.DBUS_PATH)

#     @property
#     def context(self):
#         return self.target.context

#     @dbus.service.method(DBUS_NAME,)
#     def delete(self):
#         return self.context.delete()

#     @dbus.service.method(
#         DBUS_NAME, in_signature='s',
#     )
#     def integrate_project(self, path):
#         """Import a project from the given path"""
#         return self.context.integrate_project(path)


def get_options():
    import argparse

    parser = argparse.ArgumentParser(
        description='Run coordinated DBus engine for Listener'
    )
    parser.add_argument(
        '-v',
        '--verbose',
        default=False,
        action='store_true',
        help='Enable verbose logging (for developmen/debugging)',
    )
    return parser


def main():
    options = get_options().parse_args()
    defaults.setup_logging(options, filename='dbus-service.log')
    from dbus.mainloop.glib import DBusGMainLoop

    DBusGMainLoop(set_as_default=True)
    mainloop = MAINLOOP = GLib.MainLoop()

    bus = BUS = IBus.Bus()
    ibusengine.register_engine(bus)

    ListenerService()

    def on_disconnected(bus):
        mainloop.quit()

    bus.connect('disconnected', on_disconnected)

    # TODO: we should be checking the result here, the sync method just times out
    # but the async one seems to work, just takes a while
    log.debug("Starting mainloop")
    mainloop.run()

