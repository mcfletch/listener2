"""Event sending common code"""
import socket, queue, threading, logging, os, json

log = logging.getLogger(__name__)


def create_sending_threads(sockname='/tmp/dspipe/events'):
    """Create a simple threaded server serving events at sockname"""
    outputs = []
    out_queue = queue.Queue()
    t = threading.Thread(target=write_queue, args=(out_queue, outputs))
    t.setDaemon(True)
    t.start()

    sock = create_output_socket(sockname)
    t = threading.Thread(target=output_thread, args=(sock, outputs))
    t.setDaemon(True)
    t.start()

    return out_queue


def create_output_socket(sockname):
    if os.path.exists(sockname):
        os.remove(sockname)
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(sockname)
    log.info("Serving events on %s", sockname)
    return sock


def output_thread(sock, outputs):
    sock.listen(1)
    while True:
        conn, addr = sock.accept()
        log.info("Got a connection on %s", conn)
        q = queue.Queue()
        outputs.append(q)
        threading.Thread(target=out_writer, args=(conn, q, outputs)).start()


def write_queue(queue, outputs):
    """run the write queue"""
    while True:
        record = queue.get()
        if hasattr(record, 'json'):
            for transcript in record.transcripts:
                transcript.rule_matches = []
            encoded = record.json(exclude={'rule_matches'}).encode('utf-8')
        else:
            encoded = json.dumps(record).encode('utf-8')
        for output in outputs:
            output.put(encoded)


def out_writer(conn, q, outputs):
    """Trivial thread to write events to the client"""
    while True:
        try:
            content = q.get()
            conn.sendall(content)
            conn.sendall(b'\000')
        except Exception:
            log.debug("Failed during send, closing this client: %s", conn)
            conn.close()
            break
    outputs.remove(q)
