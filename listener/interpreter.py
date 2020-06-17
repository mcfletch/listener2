"""Provide for the interpretation of incoming utterances based on user provided rules
"""
import re, logging, os, json
from . import defaults, ruleloader, models
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


# class Context(attr.s):
#     """A chaining store of context based on communication environment"""
#     parent: 'Context' = None
#     rules: 'List[RuleSet]' = None
#     history: 'List[Utterance]' = None

#     def interpret(self, event):
#         """Attempt to determine what this event likely means"""


def match_rules(words, rules):
    """Find rules which match in the rules"""
    for start in range(len(words)):
        branch = rules
        i = 0
        for i, word in enumerate(words[start:]):
            if word in branch:
                branch = branch[word]
            elif branch is not rules and ruleloader.WORD_MARKER in branch:
                branch = branch[ruleloader.WORD_MARKER]
            elif branch is not rules and ruleloader.PHRASE_MARKER in branch:
                branch = branch[ruleloader.PHRASE_MARKER]
                break
            else:
                # we don't match any further rules, do we
                # have a current match?
                i -= 1
                break
        if None in branch:
            rule = branch[None]
            return rule, words, start, start + i + 1


def apply_rules(words, rules):
    """Iteratively apply rules from rule-set until nothing changes"""
    working = words[:]
    for i in range(20):
        match = match_rules(working, rules)
        if match:
            working = match[0](*match[1:])
        else:
            break
    return working


def words_to_text(words):
    """Compress words taking no-space markers into effect..."""
    result = []
    no_space = False
    for item in words:
        if item == '^':
            no_space = True
        else:
            if not no_space:
                result.append(' ')
            result.append(item)
            no_space = False
    if not no_space:
        result.append(' ')
    return ''.join(result)


class KenLMScorer(pydantic.BaseModel):
    definition: models.ScorerDefinition = None

    _scorer = None

    @property
    def name(self):
        return self.definition.name

    @models.justonce_property
    def scorer(self):
        """Load our scorer model (a KenLM model by default)"""
        import kenlm

        model = kenlm.Model(self.definition.language_model)
        return model

    def score(self, utterance: models.Utterance):
        """Score the utterance"""
        scorer = self.scorer
        scores = []
        for transcript in utterance.transcripts:
            score = scorer.score(transcript.text)
            scores.append((score, transcript))
        return sorted(scores, key=lambda x: x[0], reverse=True)


class Context(object):
    def __init__(self, name):
        self.name = name
        self.config = models.ContextDefinition.by_name(self.name)

    SCORER_CLASSES = {
        'kenlm': KenLMScorer,
    }

    @models.justonce_property
    def rules(self):
        return ruleloader.load_rules(self.config.rules)

    @models.justonce_property
    def scorers(self):
        return [
            self.SCORER_CLASSES[scorer.type](definition=scorer)
            for scorer in self.config.scorers
            if scorer.type in self.SCORER_CLASSES
        ]

    def score(self, event):
        estimates = []
        for scorer in self.scorers:
            # Show scores and n-gram matches
            log.info("With the %s scorer", scorer.name)
            for rating, transcript in scorer.score(event)[:10]:
                log.info("%8s => %r", '%0.2f' % (rating), transcript.text)
        return sorted(estimates)

    def apply_rules(self, event):
        rules = self.rules
        for transcript in event.transcripts:
            original = transcript.words[:]
            new_words = apply_rules(transcript.words, rules)
            if new_words != original:
                transcript.text = words_to_text(new_words)
                transcript.words = new_words
            log.debug("%r => %r", words_to_text(original), transcript.text)
            break
        return event


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
        default='english-python',
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
    context = Context(options.context)
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
            if event.transcripts[0].words in ([''], ['he']):
                continue
            if not options.scorer:
                event = context.apply_rules(event)
                queue.put(event)
            else:
                context.score(event)
