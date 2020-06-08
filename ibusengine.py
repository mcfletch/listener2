#! /usr/bin/env python3
"""Host side IBus engine using the Dockerised recogpipe

Note: this daemon is LGPL because IBus is LGPL licensed
and we're importing the IBus code into the process
"""
import gi
gi.require_version('IBus','1.0')
from gi.repository import IBus
from gi.repository import GObject, GLib, Gio
IBus.init()
import json, logging, threading, time, errno, socket, select
log = logging.getLogger(__name__)

NAME='DeepSpeechPipe'
SERVICE_NAME=NAME.lower()
COMPONENT = "org.freedesktop.IBus.%s"%(NAME,)

def get_config():
    return {
        'source': 'hw:1,0',
        'target': '/tmp/dspipe/audio',
        'events': '/tmp/dspipe/events',
    }

class DeepSpeechEngine(IBus.Engine):
    __gtype_name__ = NAME
    DESCRIPTION = IBus.EngineDesc.new(
        SERVICE_NAME,
        NAME,
        'DeepSpeech English in Docker',
        'en',
        'LGPL',
        'Mike C. Fletcher',
        '', # icon
        'us', # keyboard layout
    )
    def __init__(self):
        self.config = get_config() 
        self.input = None
        self.generator = None
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
        super(DeepSpeechEngine,self).__init__()
    def do_focus_in(self):
        log.info("Focussing")
        self.wanted = True
        self.register_properties(self.properties)
        self.processing = threading.Thread(target=self.processing_thread)
        self.processing.setDaemon(True)
        self.processing.start()
    def do_focus_out(self):
        self.wanted = False
    # def do_enable(self):
    #     """Enable the input..."""

    def do_property_activate(self, prop_name, state):
        if prop_name == 'listening':
            self.wanted = bool(state)
    wanted = False
    def create_client_socket(self, sockname='/tmp/dspipe/events'):
        import socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.setblocking(False)
        sock.connect(sockname)
        return sock
    def on_decoding_event(self, event):
        """We have received an event, update IBus with the details"""
        self.debug_event(event)
        # if event.get('partial'):
        #     log.info("Partial event: %s", event)
        # else:
        #     log.info("Final event: %s", event)

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
                log.info("Opening event socket")
                sock = self.create_client_socket()
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
                                GObject.idle_add(self.on_decoding_event,decoded)
                            # log.debug("%s bytes remaining",len(content))
                    except Exception as err:
                        log.warning("Crashed during recv, closing...")
                finally:
                    log.info("Closing event socket")
                    sock.close() 
                

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
    bus.set_global_engine_async(
        SERVICE_NAME, 
        -1, 
        None, 
        None, 
        None
    ), "Unable to set the engine to %s"%(NAME,)
    log.info("Starting mainloop")
    mainloop.run()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(levelname) 7s %(name)s:%(lineno)s %(message)s',
    )
    main()
