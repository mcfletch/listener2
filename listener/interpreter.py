"""Provide for the interpretation of incoming utterances based on user provided rules
"""
import re, logging, os, json
from . import defaults, ruleloader, models, eventreceiver
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


class Interpreter(pydantic.BaseModel):
    current_context_name: str = 'english-python'
    active: bool = True
    current_context: Context = None
    sockname: str = defaults.RAW_EVENTS
    connect_backoff: float = 2.0

    def set_context(self, name):
        """Reload our currently configured context"""
        context = self.current_context = Context.by_name(self.current_context_name)
        self.current_context_name = name
        return context

    def run(self, result_queue):
        """Run the interpreter on an event stream"""
        # Start in the originally specified context
        context = self.set_context(self.current_context_name)
        for event in eventreceiver.read_from_socket(
            sockname=self.sockname, connect_backoff=self.connect_backoff,
        ):
            if event.final:
                # TODO: Need a better way to exclude silence and small speaking pops
                # The DeepSpeech language model basically has 'he' as the result for
                # lots of breath and pop sounds, but that's just an artifact of this
                # particular language model rather than the necessary result of hearing
                # the pop
                if event.transcripts[0].words in ([], [''], ['he']):
                    continue
                result_queue.put(self.process_event(context, event))
            elif event.partial:
                result_queue.put(event)
            else:
                log.info('BACKEND: %s', " ".join(getattr(event, 'messages', None)))

    def process_event(self, context, event):
        """Process a single (final) event to apply our rules/scorings
        
        This is split out so that we can easily test that we are applying the rules
        """
        context.score(event)
        for t in event.transcripts:
            log.info('%8s: %s', '%0.1f' % t.confidence, t.words)
        event = context.apply_rules(event)
        best_guess = event.best_guess()
        log.info('    ==> %s', event.best_guess().words)
        return event


def main():
    from . import eventreceiver, eventserver

    options = get_options().parse_args()
    defaults.setup_logging(options)
    queue = eventserver.create_sending_threads(defaults.FINAL_EVENTS)
    interpreter = Interpreter(current_context_name=options.context,)
    interpreter.run(queue)

