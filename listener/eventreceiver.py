"""Simple iterative reading of an open socket to produce events"""
import socket, logging, time, json, select, os
from . import defaults

log = logging.getLogger(__name__)

DEFAULT_SOCKET = defaults.RAW_EVENTS


def debug_event(event):
    log.info(
        "Event: final=%s transcripts=%s", event['final'], len(event['transcripts'])
    )
    if event.get('final', False):
        for transcript in event['transcripts']:
            log.info("   %0.3f ==> %s", transcript['confidence'], transcript['text'])
    else:
        for transcript in event['transcripts'][:1]:
            log.info("?  %0.3f ... %s", transcript['confidence'], transcript['text'])


def create_client_socket(sockname):
    """Connect to the given socket as a read-only client"""
    import socket

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.setblocking(False)
    sock.connect(sockname)
    return sock


def read_thread(callback, sockname=DEFAULT_SOCKET):
    """Utility to run callback on each read event from sockname"""
    for event in read_from_socket(sockname):
        callback(event)


def read_from_socket(
    sockname=DEFAULT_SOCKET, connect_backoff=2.0,
):
    while True:
        try:
            log.debug("Opening event socket: %s", sockname)
            sock = create_client_socket(sockname)
        except FileNotFoundError as err:
            log.info("Upstream source has not created: %s", sockname)
            time.sleep(connect_backoff)
        except Exception as err:
            log.exception("Unable to connect to event source")
            time.sleep(connect_backoff)
        else:
            log.debug("Waiting for events on %s", sock)
            read_set = [sock]
            try:
                content = b''
                while True:
                    readable, _, _ = select.select(read_set, [], [], 2)
                    if readable:
                        update = sock.recv(256)
                    else:
                        continue
                    if not update:
                        log.debug("Socket seems to have closed")
                        break
                    content += update
                    while b'\000' in content:
                        message, content = content.split(b'\000', 1)
                        decoded = json.loads(message)
                        yield decoded
            finally:
                log.info("Closing %s", sockname)
                sock.close()
                time.sleep(connect_backoff)


def get_options():
    import argparse

    parser = argparse.ArgumentParser(description='Run an IBus Engine for DeepSpeech')
    return parser


def main():
    options = get_options().parse_args()
    logging.basicConfig(
        level=logging.DEBUG, format='%(levelname) 7s %(name)s:%(lineno)s %(message)s',
    )
    read_thread(debug_event)
