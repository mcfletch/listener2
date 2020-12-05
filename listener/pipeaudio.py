#! /usr/bin/env python3
"""Low level process to create an pulse-audio feed into the recogniser daemon"""
import os, subprocess, logging, time, re
from . import defaults, exitonparentexit

log = logging.getLogger(__name__)
DEFAULT_TARGET = defaults.DEFAULT_INPUT


def ensure_target(target=DEFAULT_TARGET):
    """Ensure that target directory exists and target is a fifo in it"""
    directory = os.path.dirname(target)
    if not os.path.exists(target):
        log.info("Creating fifo in %s", target)
        directory = os.path.dirname(target)
        if not os.path.exists(directory):
            os.makedirs(directory, 0o700)
        os.mkfifo(target)
    return target


def get_options():
    import argparse

    parser = argparse.ArgumentParser(
        description='Use parec arecord to pipe audio to listener',
    )
    parser.add_argument(
        '-t',
        '--target',
        default=DEFAULT_TARGET,
        help='Named pipe to which to record (default: %s)' % (DEFAULT_TARGET,),
    )
    parser.add_argument(
        '-d',
        '--device',
        default=None,
        help='If provided, overrides the default audio device',
    )
    parser.add_argument(
        '-v',
        '--verbose',
        default=False,
        action='store_true',
        help='Enable verbose logging (for development/debugging)',
    )
    parser.add_argument(
        '--volume',
        default='100',
        type=int,
        help='Volume as a percent 0 to 100 for pacat',
    )
    return parser


def main():
    options = get_options().parse_args()
    defaults.setup_logging(options)
    exitonparentexit.exit_on_parent_exit()
    target = options.target
    ensure_target(target)
    verbose = [] if not options.verbose else ['-v']
    device = (
        [] if not options.device else ['-d', '%s' % options.device,]
    )
    command = (
        ['parec',]
        + verbose
        + device
        + [
            '--rate',
            str(defaults.SAMPLE_RATE),
            '--format',
            's16le',
            '--channels',
            '1',
            '--raw',
            '--volume',
            str(options.volume),
            '--record',
            '--client-name',
            '%s-microphone' % (defaults.APP_NAME,),
            '--stream-name',
            'recogniser',
            target,
        ]
    )
    log.info("Command: %s", " ".join(command))
    os.execvp(command[0], command)
