"""Provide for the interpretation of incoming utterances based on user provided rules
"""
import re, logging, os, json
from . import defaults

HERE = os.path.dirname(__file__)
BUILTINS = os.path.join(HERE, 'rulesets')

log = logging.getLogger(__name__)


class MissingRules(OSError):
    """Raised if we cannot find the rules-file"""


def does_not_escape(base, relative):
    """Check that relative does not escape from base (return combined or raise error)"""
    base = base.rstrip('/')
    if not base:
        raise ValueError("Need a non-root base path")
    combined = os.path.abspath(os.path.normpath(os.path.join(base, relative)))
    root = os.path.abspath(os.path.normpath(base))
    if os.path.commonpath([root, combined]) != root:
        raise ValueError(
            "Path %r would escape from %s, not allowed" % (relative, base,)
        )
    return combined


def named_ruleset_file(relative):
    assert relative is not None
    for source in [
        does_not_escape(defaults.CONTEXT_DIR, '%s.rules' % (relative,)),
        does_not_escape(BUILTINS, '%s.rules' % (relative,)),
    ]:
        if os.path.exists(source):
            return source
    log.warning('Unable to find rules-file for %s', relative)
    raise MissingRules(relative)
    # return None


def text_entry_rule(match, target):
    """Create a rule from the text-entry mini-language"""
    no_space_before = target.startswith('^')
    no_space_after = target.endswith('^')
    text = bytes(target.strip('^')[1:-1], 'utf-8').decode('unicode_escape')

    def apply_rule(words, start_index=0, end_index=-1):
        """Given a match on the rule, produce modified result"""
        prefix = words[:start_index]
        suffix = words[end_index:]
        result = []
        if no_space_before:
            result.append('^')
        result.append(text)
        if no_space_after:
            result.append('^')
        return prefix + result + suffix

    apply_rule.__name__ = 'text_entry_%s' % ("_".join(match))
    apply_rule.match = match
    apply_rule.text = text
    apply_rule.target = target
    apply_rule.no_space_after = no_space_after
    apply_rule.no_space_before = no_space_before
    return apply_rule


def null_transform(words):
    """Used when the user references an unknown transformation"""
    return words


def transform_rule(match, target):
    no_space_before = target.startswith('^')
    no_space_after = target.endswith('^')
    try:
        transformation = NAMED_RULES[target.rstrip('()')]
    except KeyError:
        log.error(
            "The rule %s => %s references an unknown function", " ".join(match), target
        )
        transformation = null_transform

    phrase = match[-1] == PHRASE_MARKER
    word = match[-1] == WORD_MARKER

    def apply_rule(words, start_index=0, end_index=-1):
        """Given a match, transform and return the results"""
        working = words[:]
        if phrase:
            working[start_index:] = transformation(words[end_index - 1 :])
        else:
            working[start_index:end_index] = transformation(
                words[end_index - 1 : end_index]
            )
        return working

    apply_rule.__name__ = 'transform_entry_%s' % ("_".join(match))
    apply_rule.match = match
    apply_rule.target = target
    apply_rule.text = None
    apply_rule.no_space_after = no_space_after
    apply_rule.no_space_before = no_space_before

    return apply_rule


def format_rules(rules):
    """Format ruleset into format for storage"""
    for match, target in rules:
        yield '%s => %s' % (' '.join(match), target)


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


NAMED_RULES = {}


def named_rule(function):
    NAMED_RULES[function.__name__] = function
    return function


@named_rule
def title(words):
    return [word.title() for word in words]


@named_rule
def all_caps(words):
    return [word.upper() for word in words]


@named_rule
def constant(words):
    return ['^', '_'.join([x for x in all_caps(words) if x != '^']), '^']


@named_rule
def camel(words):
    result = []
    for word in words:
        result.append(word.title())
        result.append('^')
    if words:
        del result[-1]
    return result


@named_rule
def camel_lower(words):
    return [words[0], '^'] + camel(words[1:])


@named_rule
def underscore_name(words):
    return ['^', '_'.join([x for x in words if x != '^']), '^']


@named_rule
def percent_format(name):
    return ['%(', '^', name, '^', ')s']


def iter_rules(name, includes=False):
    filename = named_ruleset_file(name)
    if filename:
        command_set = open(filename, encoding='utf-8').read()
        for i, line in enumerate(command_set.splitlines()):
            line = line.strip()
            if line.startswith('#include '):
                if includes:
                    try:
                        for pattern, target, sub_name in iter_rules(line[9:].strip()):
                            yield pattern, target, sub_name
                    except MissingRules as err:
                        err.args += ('included from %s#%i' % (name, i + 1),)
                        raise
                else:
                    log.info("Ignoring include: %s", line)
            if (not line) or line.startswith('#'):
                continue
            try:
                pattern, target = line.split('=>', 1)
            except ValueError as err:
                log.warning("Unable to parse rule #%i: %r", i + 1, line)
                continue
            pattern = pattern.strip().split()
            target = target.strip()
            # log.debug("%s => %s", pattern, target)
            yield pattern, target, name


def load_rules(name, rules=None, includes=True):
    """load a set of commands from a named rule-set"""
    rules = rules or {}
    rule_order = []
    for pattern, target, name in iter_rules(name, includes=True):
        branch = rules
        for word in pattern:
            branch = branch.setdefault(word, {})
        if target.strip('^').endswith('()'):
            rule = transform_rule(pattern, target[:-2])
        else:
            rule = text_entry_rule(pattern, target)
        branch[None] = rule
        rule.source = name
        rule_order.append(rule)
    return rules, rule_order


# class Context(attr.s):
#     """A chaining store of context based on communication environment"""
#     parent: 'Context' = None
#     rules: 'List[RuleSet]' = None
#     history: 'List[Utterance]' = None

#     def interpret(self, event):
#         """Attempt to determine what this event likely means"""

PHRASE_MARKER = '${phrase}'
WORD_MARKER = '${word}'


def match_rules(words, rules):
    """Find rules which match in the rules"""
    for start in range(len(words)):
        branch = rules
        i = 0
        for i, word in enumerate(words[start:]):
            if word in branch:
                branch = branch[word]
            elif branch is not rules and WORD_MARKER in branch:
                branch = branch[WORD_MARKER]
            elif branch is not rules and PHRASE_MARKER in branch:
                branch = branch[PHRASE_MARKER]
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


class Context(object):
    def __init__(self, name):
        self.name = name
        if name == 'core':
            self.directory = os.path.join(HERE, 'contexts', name)
        else:
            self.directory = os.path.join(defaults.CONTEXT_DIR, name)
        self.config_file = os.path.join(self.directory, 'config.json')
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            self.config = json.loads(open(self.config_file).read())
        else:
            self.config = {}

    def save_config(self):
        if self.name == 'core':
            return False
        content = json.dumps(self.config, indent=2, sort_keys=True)
        with open(self.config_file + '~', 'w') as fh:
            fh.write(content)
        os.rename(self.config_file + '~', self.config_file)
        return True

    _scorers = None

    @property
    def scorers(self):
        """Load our scorer model (a KenLM model by default)"""
        if self._scorers is None:
            import kenlm

            models = []
            for source in self.config.get('scorers', [defaults.CACHED_SCORER_FILE]):
                model = kenlm.Model(source)
                models.append(model)
            self._scorers = models
        return self._scorers

    _rules = None
    _ruleset = None

    @property
    def rules(self):
        if self._rules is None:
            self._rules, self._rule_set = load_rules(
                self.config.get('rules', 'default')
            )
        return self._rules

    def score(self, event):
        estimates = []
        for scorer in self.scorers:
            # Show scores and n-gram matches
            for transcript in event['transcripts']:
                log.debug("Trans: %r", transcript['text'])
                score = scorer.score(transcript['text'])
                estimates.append((score, transcript))
        return sorted(estimates)

    def apply_rules(self, event):
        rules = self.rules
        for transcript in event['transcripts']:
            original = transcript['words'][:]
            new_words = apply_rules(transcript['words'], rules)
            if new_words != original:
                transcript['text'] = words_to_text(new_words)
                transcript['words'] = new_words
            log.debug("%r => %r", words_to_text(original), transcript['text'])
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
    from . import eventreceiver, eventserver
    import json

    context = Context('core')
    if not options.scorer:
        queue = eventserver.create_sending_threads(defaults.FINAL_EVENTS)
    else:
        queue = None
    for event in eventreceiver.read_from_socket(
        sockname=defaults.RAW_EVENTS, connect_backoff=2.0,
    ):
        if not event.get('partial'):
            # TODO: Need a better way to exclude silence and small speaking pops
            # The DeepSpeech language model basically has 'he' as the result for
            # lots of breath and pop sounds, but that's just an artifact of this
            # particular language model rather than the necessary result of hearing
            # the pop
            if event['transcripts'][0]['words'] in ([''], ['he']):
                continue
            if not options.scorer:
                event = context.apply_rules(event)
                queue.put(event)
            else:
                context.score(event)
