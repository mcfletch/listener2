"""Constants and shared definitions"""
import os, logging

USER_RUN_DIR = os.environ.get('XDG_RUNTIME_DIR', '/run/user/%s' % (os.geteuid()))
RUN_DIR = os.path.join(USER_RUN_DIR, 'recogpipe')
DEFAULT_INPUT = os.path.join(RUN_DIR, 'audio')
DEFAULT_OUTPUT = os.path.join(RUN_DIR, 'events')


def setup_logging(options):
    logging.basicConfig(
        level=logging.DEBUG if options.verbose else logging.WARNING,
        format='%(asctime)s:%(levelname)s:%(name)s:%(lineno)s %(message)s',
    )
