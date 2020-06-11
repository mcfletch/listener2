#! /usr/bin/env python3
"""Non-working attempt to get a clean/signal-able ffmpeg to named pipe pipeline"""
import os, subprocess, logging, time, re
from . import defaults

log = logging.getLogger(__name__)

DEFAULT_TARGET = '/run/user/%s/recogpipe/audio' % (os.geteuid(),)


def get_options():
    import argparse

    parser = argparse.ArgumentParser(
        description='Use ALSA arecord to pipe audio to recogpipe',
    )
    parser.add_argument(
        '-t',
        '--target',
        default=DEFAULT_TARGET,
        help='Named pipe to which to record (default: %s)' % (DEFAULT_TARGET,),
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
    defaults.setup_logging(options)
    target = options.target
    directory = os.path.dirname(target)
    if not os.path.exists(target):
        log.info("Creating fifo in %s", target)
        os.mkfifo(target)
    command = [
        'parec',
        '-v',
        '--rate',
        '16000',
        '--format',
        's16le',
        '--channels',
        '1',
        '--raw',
        '--record',
        '--client-name',
        'recgpipe-microphone',
        '--stream-name',
        'primary',
        target,
    ]
    log.info("Command: %s", " ".join(command))
    os.execvp(command[0], command)
