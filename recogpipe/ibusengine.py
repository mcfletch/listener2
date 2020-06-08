#! /usr/bin/env python3
"""Host side IBus engine using the Dockerised recogpipe

Note: this daemon is LGPL because IBus is LGPL licensed
and we're importing the IBus code into the process, though
I suppose we're using gobject-introspection and the DBus
to do the communication normally. Still, LGPL is fine
and makes things consistent.
"""
import gi
gi.require_version('IBus','1.0')
from gi.repository import IBus
from gi.repository import GObject, GLib, Gio
IBus.init()
import json, logging, threading, time, errno, socket, select, os
log = logging.getLogger(__name__ if __name__ != '__main__' else 'ibus')

NAME='DeepSpeechPipe'
SERVICE_NAME=NAME.lower()
COMPONENT = "org.freedesktop.IBus.%s"%(NAME,)

USER_RUN_DIR = os.environ.get('XDG_RUNTIME_DIR','/run/user/%s'%(os.geteuid()))
RUN_DIR = os.path.join(USER_RUN_DIR,'recogpipe')
DEFAULT_INPUT = os.path.join(RUN_DIR,'audio')
DEFAULT_OUTPUT = os.path.join(RUN_DIR,'events')

def get_config():
    return {
        'source': 'hw:1,0',
        'target': DEFAULT_INPUT,
        'events': DEFAULT_OUTPUT,
    }

class DeepSpeechEngine(IBus.Engine):
    """Provides an IBus Input Method Engine using RecogPipe backend
    
    There is a *lot* of complexity in the IBus API that we still
    need to get sorted out. For instance, should we use IBus
    alternatives system, or write a custom GUI for doing the 
    partial and final sets
    """
    __gtype_name__ = NAME
    DESCRIPTION = IBus.EngineDesc.new(
        SERVICE_NAME,
        NAME,
        'DeepSpeech English',
        'en',
        'LGPL',
        'Mike C. Fletcher',
        '', # icon
        'us', # keyboard layout
    )
    wanted = False
    def __init__(self):
        self.config = get_config() 
        self.properties = IBus.PropList()
        self.properties.append(IBus.Property(
            key='source',
            type=IBus.PropType.NORMAL,
            label='Microphone',
            tooltip='ALSA device such as hw:0,0 or hw:1,0 (see arecord -l for ids)',
            visible=True,
        ))
        self.properties.append(IBus.Property(
            key='listening',
            type=IBus.PropType.TOGGLE,
            label='Listen',
            tooltip='Toggle whether the engine is currently listening',
            visible=True,
        ))
        self.lookup_table = IBus.LookupTable.new(
            5, # size
            0, # index,
            True, # cursor visible
            True, # round
        )
        self.lookup_table_content = []
        # self.lookup_table.ref_sink()
        super(DeepSpeechEngine,self).__init__()
    
    processing = None
    def do_focus_in(self):
        log.info("Focus")
        # IBus.Engine.do_focus_in(self)
        self.wanted = True
        self.register_properties(self.properties)
        self.hide_lookup_table()
        self.hide_preedit_text()
        if not self.processing:
            self.processing = threading.Thread(target=self.processing_thread)
            self.processing.setDaemon(True)
            self.processing.start()

    def do_focus_out(self):
        log.info("Focus lost")
        # IBus.Engine.do_focus_out(self)
        # IBus.Engine.do_focus_out(self)
        self.wanted = False
    def do_enable(self):
        """Enable the input..."""
        log.info("Enabling")
        # IBus.Engine.do_enable(self)
        self.wanted = True
        # self.surrounding_text =self.get_surrounding_text()
        
    def do_disable(self):
        self.wanted = True
        IBus.Engine.do_disable(self)

    # def do_set_surrounding_text(self, text, cursor_index, anchor_pos):
    #     """Handle engine setting the surrounding text"""
    #     log.info("Got surrounding text: %s at %s", text.get_text(),cursor_index)
    #     self.surrounding_text = text,cursor_index,anchor_pos

    def do_property_activate(self, prop_name, state):
        log.info("Set property: %s = %r",prop_name, state)
        # if prop_name == 'listening':
        #     self.wanted = bool(state)
    def create_client_socket(self, sockname):
        import socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.setblocking(False)
        sock.connect(sockname)
        return sock
    
    def on_decoding_event(self, event):
        """We have received an event, update IBus with the details"""
        # if not self.enabled:
        #     log.debug("Not enabled")
        #     return 
        # if not self.has_focus:
        #     log.debug("Not focussed")
        #     return 
        self.debug_event(event)
        if not self.wanted:
            return
        choices = self.all_transcripts(event)
        self.show_choices(choices)
    def show_choices(self, choices):
        if choices != self.lookup_table_content:
            self.lookup_table.clear()
            for choice in choices:
                self.lookup_table.append_label(IBus.Text.new_from_string(choice))
            self.update_lookup_table(self.lookup_table,True)
            self.lookup_table_content = choices 
        if len(choices) > 1 or choices[0] != '':
            log.info("Show table")
            self.show_lookup_table()
        else:
            log.info("Hide table")
            self.hide_lookup_table()

    def first_transcript(self, event):
        for transcript in event['transcripts']:
            return transcript['text']
    def all_transcripts(self, event):
        return [
            transcript['text']
            for transcript in event['transcripts']
        ]

    def debug_event(self, event):
        log.info("Event: final=%s transcripts=%s",event['final'],len(event['transcripts']))
        if event.get('final',False):
            for transcript in event['transcripts']:
                log.info("   %0.3f ==> %s",transcript['confidence'],transcript['text'])
        else:
            for transcript in event['transcripts'][:1]:
                log.info("?  %0.3f ... %s",transcript['confidence'],transcript['text'])

    def processing_thread(self):
        """Thread which listens to the server and updates our state"""
        while self.wanted:
            try:
                log.info("Opening event socket: %s", self.config['events'])
                sock = self.create_client_socket(
                    self.config['events']
                )
            except Exception as err:
                log.exception("Unable to connect to event source")
                time.sleep(5)
            else:
                log.debug("Waiting for events on %s", sock)
                try:
                    content = b''
                    try:
                        while self.wanted:
                            readable = False 
                            try:
                                update = sock.recv(1024)
                            except socket.error:
                                time.sleep(.2 if not content else .02)
                                continue

                            if not update:
                                log.info("Socket seems to have closed")
                                break
                            content += update 
                            while b'\000' in content:
                                message,content = content.split(b'\000',1)
                                decoded = json.loads(message)
                                GLib.idle_add(self.on_decoding_event,decoded)
                            # log.debug("%s bytes remaining",len(content))
                    except Exception as err:
                        log.warning("Crashed during recv, closing...")
                finally:
                    log.info("Closing event socket")
                    sock.close() 
                    time.sleep(2)
        self.processing = None

def main():
    log.info('Registering the component')
    component = IBus.Component(
        name = COMPONENT,
        description='DeepSpeech-in-docker input method',
        version='1.0',
        license='LGPL',
        author='Mike C. Fletcher',
        homepage='https://github.com/mcfletch/deepspeech-docker',
        command_line='/opt/deepspeech-docker/engine.py',
        textdomain='en', # TODO: is this language?
    )
    component.add_engine(DeepSpeechEngine.DESCRIPTION)

    mainloop = GLib.MainLoop()
    bus = IBus.Bus()
    def on_disconnected(bus):
        mainloop.stop()
    bus.connect('disconnected',on_disconnected)
    connection = bus.get_connection()
    assert connection, "IBus has no connection"
    factory = IBus.Factory.new(connection)
    factory.add_engine(
        SERVICE_NAME,
        GObject.type_from_name(NAME)
    ), "Unable to add the engine"

    assert bus.register_component(component), "Unable to register our component"
    def on_set_engine(source,result,data=None):
        if result.had_error():
            log.error("Unable to register!")
            mainloop.stop()
        log.info("Registration result: %s", dir(result))
    def set_engine():
        assert bus.set_global_engine_async(
            SERVICE_NAME, 
            5000, # shouldn't take this long! 
            None, 
            on_set_engine, 
            None
        )
    # TODO: we should be checking the result here, the sync method just times out
    # but the async one seems to work, just takes a while
    log.info("Starting mainloop")
    GLib.idle_add(set_engine)
    mainloop.run()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(levelname) 7s %(name)s:%(lineno)s %(message)s',
    )
    main()
