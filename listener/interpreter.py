"""Provide for the interpretation of incoming utterances based on user provided rules
"""
import re, logging, os, json
from . import defaults, ruleloader, models
from .context import Context
import pydantic

log = logging.getLogger(__name__)


# General commands that don't recognise well
BAD_COMMANDS = """
press tab
dedent
comma
backspace
word left
word right
line start 
line end
octothorpe => ^'#'
shebang => ^'#!'
"""


def get_options():
    import argparse

    parser = argparse.ArgumentParser(
        description='Run the interpreter outside of the DBus service',
    )
    parser.add_argument(
        '-s',
        '--scorer',
        default=False,
        action='store_true',
        help='If specified, then just do score debugging and do not produce clean events',
    )
    parser.add_argument(
        '--debug-scores',
        default=False,
        action='store_true',
        help='Debug sub-component scoring',
    )
    parser.add_argument(
        '-v',
        '--verbose',
        default=False,
        action='store_true',
        help='Enable verbose logging (for developmen/debugging)',
    )
    parser.add_argument(
        '--context',
        default='english-general',
        choices=sorted(models.ContextDefinition.context_names()),
        help='Context in which to start processing',
    )
    return parser


def main():
    options = get_options().parse_args()
    defaults.setup_logging(options)
    from . import eventreceiver, eventserver
    import json

    # Start in the wikipedia context...
    context = Context.by_name(options.context)
    if not options.scorer:
        queue = eventserver.create_sending_threads(defaults.FINAL_EVENTS)
    else:
        queue = None
    for event in eventreceiver.read_from_socket(
        sockname=defaults.RAW_EVENTS, connect_backoff=2.0,
    ):
        if not event.partial:
            # TODO: Need a better way to exclude silence and small speaking pops
            # The DeepSpeech language model basically has 'he' as the result for
            # lots of breath and pop sounds, but that's just an artifact of this
            # particular language model rather than the necessary result of hearing
            # the pop
            if event.transcripts[0].words in ([], [''], ['he']):
                continue
            context.score(event)
            best_guess = event.best_guess()
            for t in event.transcripts:
                log.info('%8s: %s', '%0.1f' % t.confidence, t.words)
            event = context.apply_rules(event)
            log.info('    ==> %s', event.best_guess().words)
            queue.put(event)
