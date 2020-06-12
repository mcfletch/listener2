#! /usr/bin/env python3
"""Host side IBus engine using the Dockerised listener

Note: this daemon is LGPL because IBus is LGPL licensed
and we're importing the IBus code into the process, though
I suppose we're using gobject-introspection and the DBus
to do the communication normally. Still, LGPL is fine
and makes things consistent.

we will need to revisit how this engine is laid out
and likely create our own panel applet to provide a richer
input environment and natural controls and to provide a
tooltip showing the current partial recognition

at that point this engine will be primarily responsible
for keeping track of where text was inserted (so that we can
remove the text if we need to do a correction).
"""
import gi

gi.require_version('IBus', '1.0')
from gi.repository import IBus
from gi.repository import GObject, GLib, Gio

IBus.init()
from . import eventreceiver, interpreter
import json, logging, threading, time, errno, socket, select, os

log = logging.getLogger(__name__ if __name__ != '__main__' else 'ibus')

BUS = None
MAINLOOP = None
NAME = 'Listener'
SERVICE_NAME = NAME.lower()
COMPONENT = "org.freedesktop.IBus.%s" % (NAME,)

USER_RUN_DIR = os.environ.get('XDG_RUNTIME_DIR', '/run/user/%s' % (os.geteuid()))
RUN_DIR = os.path.join(USER_RUN_DIR, 'listener')
DEFAULT_PIPE = os.path.join(RUN_DIR, 'clean-events')


class ListenerEngine(IBus.Engine):
    """Provides an IBus Input Method Engine using Listener backend
    
    There is a *lot* of complexity in the IBus API that we still
    need to get sorted out. For instance, should we use IBus
    alternatives system, or write a custom GUI for doing the 
    partial and final sets
    """

    __gtype_name__ = NAME
    DESCRIPTION = IBus.EngineDesc.new(
        SERVICE_NAME,
        NAME,
        'English Listener',
        'en',
        'LGPL',
        'Mike C. Fletcher',
        '',  # icon
        'us',  # keyboard layout
    )
    wanted = False

    def __init__(self):
        """initialize the newly created engine

        """
        self.properties = IBus.PropList()
        # self.properties.append(IBus.Property(
        #     key='source',
        #     type=IBus.PropType.NORMAL,
        #     label='Microphone',
        #     tooltip='ALSA device such as hw:0,0 or hw:1,0 (see arecord -l for ids)',
        #     visible=True,
        # ))
        self.properties.append(
            IBus.Property(
                key='listening',
                type=IBus.PropType.TOGGLE,
                label='DeepSpeech',
                tooltip='Toggle whether the engine is currently listening',
                visible=True,
            )
        )
        # self.lookup_table = IBus.LookupTable.new(
        #     5, 0, True, True,  # size  # index,  # cursor visible  # round
        # )
        # self.lookup_table_content = []
        # self.interpreter_rules, self.rule_set = interpreter.load_rules(
        #     interpreter.good_commands,
        # )
        # self.lookup_table.ref_sink()
        super(ListenerEngine, self).__init__()

    processing = None
    no_space = False

    def do_focus_in(self):
        log.debug("engine received focus")
        # IBus.Engine.do_focus_in(self)
        self.wanted = True
        self.register_properties(self.properties)
        # self.hide_lookup_table()
        self.hide_preedit_text()
        if not self.processing:
            self.processing = threading.Thread(
                target=eventreceiver.read_thread,
                kwargs=dict(sockname=DEFAULT_PIPE, callback=self.schedule_event,),
            )
            self.processing.setDaemon(True)
            self.processing.start()

    def do_focus_out(self):
        log.debug("the engine lost focus")
        self.wanted = False

    def do_enable(self):
        log.debug("the engine was enabled")
        # IBus.Engine.do_enable(self)
        self.wanted = True
        self.surrounding_text = self.get_surrounding_text()
        log.debug("Surrounding text: %s", self.surrounding_text)

    def do_disable(self):
        log.debug("the engine was disabled")
        self.wanted = False

    def do_set_surrounding_text(self, text, cursor_index, anchor_pos):
        """Handle engine setting the surrounding text"""
        log.info("Got surrounding text: %s at %s", text.get_text(), cursor_index)
        self.surrounding_text = text, cursor_index, anchor_pos

    def do_property_activate(self, prop_name, state):
        log.info("Set property: %s = %r", prop_name, state)

    def create_client_socket(self, sockname):
        """open a unix socket to the given socket name"""
        import socket

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.setblocking(False)
        sock.connect(sockname)
        return sock

    def schedule_event(self, event):
        """Called from the receiver thread to do our callback"""
        GLib.idle_add(self.on_decoding_event, event)

    def on_decoding_event(self, event):
        """We have received an event, update IBus with the details"""
        if not event.get('partial'):
            transcript = self.first_transcript(event)
            # ick, 'he' is the default in the particular 0.7.3 released language model... meh
            to_send = []
            log.debug('Words: %s', transcript['words'])
            for word in transcript['words']:
                if word == '^':
                    self.no_space = True
                elif isinstance(word, str):
                    if not self.no_space:
                        to_send.append(' ')
                    to_send.append(word)
                    self.no_space = False
                else:
                    log.info("Should do key-forwarding or the like here: %s", word)
                    # When we do meta-manipulation we have "tapped a key"
                    self.no_space = True
            # TODO: if confidence below some threshold, then we want to
            # show options, but that doesn't seem to work at all :(
            # best_guess = interpreter.words_to_text(
            #     interpreter.apply_rules(best_guess,self.interpreter_rules)
            # )
            # log.debug("> %s", best_guess)
            block = ''.join(to_send)
            log.debug('> %s', block)
            self.commit_text(IBus.Text.new_from_string(''.join(block)))

    def first_transcript(self, event):
        for transcript in event['transcripts']:
            return transcript


def get_options():
    import argparse

    parser = argparse.ArgumentParser(description='Run an IBus Engine for DeepSpeech')
    parser.add_argument(
        '-v',
        '--verbose',
        default=False,
        action='store_true',
        help='Enable verbose logging (for developmen/debugging)',
    )
    parser.add_argument(
        '-r',
        '--raw',
        default=False,
        action='store_true',
        help='Use raw (not cleaned) events for dictation (insert the raw DeepSpeech output)',
    )
    parser.add_argument(
        '-l',
        '--live',
        default=False,
        action='store_true',
        help='If true, register on the DBus name %s and interact as a regular engine'
        % (COMPONENT,),
    )
    return parser


def register_engine(bus, live=False):
    log.debug('Registering the component')
    component = IBus.Component(
        name=COMPONENT,
        description='DeepSpeech-in-docker input method',
        version='1.0',
        license='LGPL',
        author='Mike C. Fletcher',
        homepage='https://github.com/mcfletch/deepspeech-docker',
        command_line='listener-ibus -r',
        textdomain='en',  # TODO: is this language?
    )
    component.add_engine(ListenerEngine.DESCRIPTION)
    connection = bus.get_connection()
    assert connection, "IBus has no connection"
    factory = IBus.Factory.new(connection)
    factory.add_engine(
        SERVICE_NAME, GObject.type_from_name(NAME)
    ), "Unable to add the engine"
    if not live:
        assert bus.register_component(component), "Unable to register our component"

        def on_set_engine(source, result, data=None):
            if result.had_error():
                log.error("Unable to register!")
                MAINLOOP.quit()

        def set_engine():
            log.info("Registering IBus Service at %s", SERVICE_NAME)
            bus.set_global_engine_async(
                SERVICE_NAME,
                5000,  # shouldn't take this long!
                None,
                on_set_engine,
                None,
            )

        GLib.idle_add(set_engine)
    else:
        GLib.idle_add(
            bus.request_name, COMPONENT, IBus.BusNameFlag.ALLOW_REPLACEMENT,
        )


def main():
    options = get_options().parse_args()
    logging.basicConfig(
        level=logging.DEBUG if options.verbose else logging.WARNING,
        format='%(levelname) 7s %(name)s:%(lineno)s %(message)s',
    )
    if options.raw:
        log.warning("Dictating with raw DeepSpeech output")
        global DEFAULT_PIPE
        DEFAULT_PIPE = os.path.join(RUN_DIR, 'events')

    global BUS, MAINLOOP
    mainloop = MAINLOOP = GLib.MainLoop()
    bus = BUS = IBus.Bus()

    def on_disconnected(bus):
        mainloop.quit()

    bus.connect('disconnected', on_disconnected)

    # TODO: we should be checking the result here, the sync method just times out
    # but the async one seems to work, just takes a while
    log.debug("Starting mainloop")
    GLib.idle_add(register_engine, bus, False)
    mainloop.run()


if __name__ == "__main__":
    main()
