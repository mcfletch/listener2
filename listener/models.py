"""Data-model class for a rule"""
import pydantic, os, logging, json
from typing import List, Optional, Callable, Dict, Union
from . import defaults

log = logging.getLogger(__name__)

KENLM = 'kenlm'


def null_transform(words, start_index=0, end_index=0):
    """Used when the user references an unknown transformation
    
    Always returns the incoming content without modification
    """
    return words


def justonce_property(function):
    """Property that only runs function once per instance unless deleted
    
    Note: the value None is *not* accepted as a 
    result, so it will result in the function 
    being run until something else is returned.
    """
    key = '__%s_value' % (function.__name__,)

    def getter(self):
        current = self.__dict__.get(key)
        if current is None:
            self.__dict__[key] = current = function(self)
        return current

    def setter(self, value):
        self.__dict__[key] = value

    def deller(self):
        try:
            del self.__dict__[key]
        except KeyError:
            raise AttributeError(key)

    return property(fget=getter, fset=setter, fdel=deller, doc=function.__doc__,)


class AppState(pydantic.BaseModel):
    """Describes an overall application state"""

    key: str = ''
    icon: str = ''
    text: str = ''
    tooltip: str = ''


class Rule(pydantic.BaseModel):
    """Represents a single (user defined) rule for interpreting dictation
    
    Special fragments in the match can match against  wildcard
    values such as a single or multiple word fragment.

        defaults.PHRASE_MARKER
        defaults.WORD_MARKER
    """

    match: List[str] = []
    target: str = ''  # textual definition of the target
    text: Optional[Union[str, List[str]]]
    no_space_after: bool = False
    no_space_before: bool = False
    caps_after: bool = False
    process: List[Callable] = [null_transform]
    source: str = ''
    boost: float = 1.0

    def format(self):
        """Format as content for a textual rules-file"""
        return '%s: %s => %s' % (self.source, ' '.join(self.match), self.target)

    def __str__(self):
        return self.format()

    def __hash__(self):
        return hash(
            (tuple(self.match), self.target, self.no_space_after, self.no_space_before)
        )

    def __call__(self, *args, **named):
        """Call our processing function"""
        try:
            target = self.process[0]
            return target(*args, **named)
        except Exception as err:
            err.args += (self,)
            raise

    def boost_words(self):
        """Calculate the set of words that should be boosted in frequency"""
        for fragment in self.match:
            if fragment not in [defaults.WORD_MARKER, defaults.PHRASE_MARKER]:
                yield fragment, self.boost


class Transcript(pydantic.BaseModel):
    """Represents a potential transcript for an utterance"""

    partial: bool = False
    final: bool = True
    text: str = ''  # debugging text
    tokens: List[str] = []  # tokens predicted by backend
    starts: List[float] = []  # relative starts of tokens
    words: List[str] = []  # space-separated blocks
    word_starts: List[float] = []  # start of each space-separated block
    confidence: float = 0.0  # estimate of confidence for the whole transcript...

    rule_matches: List['RuleMatch'] = []  # set of matched rules...

    @classmethod
    def dbus_struct_signature(cls):
        """Describe our dbus type signature"""
        return 'bdas'

    def dbus_struct(self):
        """Create our dbus structure"""
        return (
            self.final,
            self.confidence,
            self.words,
        )

    @classmethod
    def from_dbus_struct(cls, struct):
        """Reconstitute from a dbus structure"""
        return cls(
            final=struct[0],
            partial=not struct[0],
            confidence=struct[1],
            words=struct[2],
        )


class Utterance(pydantic.BaseModel):
    """Represents a single utterance detected by the backend"""

    utterance_number: int = 0
    partial: bool = False
    final: bool = True
    transcripts: List[Transcript] = []
    messages: Optional[List[str]] = []

    def sort(self):
        """Apply sorting to our transcripts
        
        uses transcript.confidence to reverse-sort the transcripts
        such that the highest-confidence is first
        """
        self.transcripts.sort(key=lambda x: x.confidence, reverse=True)

    def best_guess(self):
        """Give our current best-guess"""
        return self.transcripts[0]

    @classmethod
    def dbus_struct_signature(cls):
        """Describe our dbus type signature"""
        return '(iba(%s)as)' % (Transcript.dbus_struct_signature())

    def dbus_struct(self):
        """Create our dbus structure"""
        return (
            self.utterance_number,
            self.final,
            [transcript.dbus_struct() for transcript in self.transcripts],
            self.messages,
        )

    @classmethod
    def from_dbus_struct(cls, struct):
        """Reconstitute from a dbus structure"""
        return cls(
            utterance_number=struct[0],
            final=struct[1],
            partial=not struct[1],
            transcripts=[Transcript.from_dbus_struct(x) for x in struct[2]],
        )


class Dictionary(pydantic.BaseModel):
    words: set = None

    def __contains__(self, word):
        return word in self.words

    def have_words(self, *words):
        result = []
        for word in words:
            if word in self.words:
                result.append(word)
        return result


class ScorerDefinition(pydantic.BaseModel):
    """Defines a scorer for a particular context
    
    type -- key into context.Context.
    
    """

    type: str = KENLM
    name: str = 'default'
    language_model: Optional[str] = defaults.CACHED_SCORER_FILE
    command_bias: Optional[float] = 1.0

    @classmethod
    def by_name(cls, name):
        name = os.path.basename(name)
        for path in [defaults.MODEL_CACHE]:  # some shared storage too
            if name == 'upstream':
                filename = defaults.CACHED_SCORER_FILE
            else:
                filename = os.path.join(path, '%s.scorer' % (name))
            if os.path.exists(filename):
                return cls(name=name, language_model=filename, type=KENLM,)
            else:
                log.info("No file: %s", filename)
        raise ValueError("Uknown scorer: %s" % (name,))


class ContextDefinition(pydantic.BaseModel):
    """A biasing  context which modifies the of a particular transcription

    """

    name: str = ''
    scorers: List[ScorerDefinition] = []
    rules: str = 'default'
    only_matches: bool = False

    @classmethod
    def context_names(cls):
        """Return the ContextDefinitions for all contexts known"""
        seen = set()
        for directory in [
            defaults.CONTEXT_DIR,
            defaults.BUILTIN_CONTEXTS,
        ]:
            if not os.path.exists(directory):
                log.warning("Expected directory %s is missing", directory)
                continue
            for name in os.listdir(directory):
                filename = os.path.join(directory, name)
                if os.path.isdir(filename):
                    if name not in seen:
                        yield name
                        seen.add(name)

    @classmethod
    def all_contexts(cls):
        """Return all defined contexts (user and built-in)"""
        result = []
        for name in cls.context_names():
            result.append(cls.by_name(name=name))
        return result

    @classmethod
    def write_default_contexts(cls):
        """Write our default contexts to disk"""
        code = ContextDefinition(
            name='english-python',
            scorers=[
                ScorerDefinition.by_name('code'),
                ScorerDefinition(name='commands', type='commands',),
            ],
            rules='code',
        )
        code.save()
        default = ContextDefinition(
            name='english-general',
            scorers=[
                ScorerDefinition.by_name('default'),
                ScorerDefinition(name='commands', type='commands',),
            ],
            rules='default',
        )
        default.save()
        # default = ContextDefinition(
        #     name='english-upstream',
        #     scorers=[
        #         ScorerDefinition.by_name('upstream'),
        #         ScorerDefinition(name='commands', type='commands',),
        #     ],
        #     rules='default',
        # )
        # default.save()
        stopped = ContextDefinition(
            name='english-stopped',
            scorers=[
                ScorerDefinition.by_name('default'),
                ScorerDefinition(name='commands', type='commands',),
            ],
            rules='stopped',
        )
        stopped.save()
        spelling = ContextDefinition(
            name='english-spelling',
            scorers=[
                ScorerDefinition.by_name('default'),
                ScorerDefinition(name='commands', type='commands',),
            ],
            rules='spelling',
        )
        spelling.save()

    @classmethod
    def directory(cls, name):
        """Calculate our directory"""
        core = os.path.join(defaults.BUILTIN_CONTEXTS, name)
        if os.path.exists(core):
            return core
        else:
            return os.path.join(defaults.CONTEXT_DIR, name)

    @classmethod
    def config_file(cls, name):
        """Calculate the configuration file for the given name"""
        return os.path.join(cls.directory(name), 'config.json')

    @classmethod
    def by_name(cls, name):
        """Load configuration from the named file"""
        filename = cls.config_file(name)
        if os.path.exists(filename):
            content = json.loads(open(filename).read())
            config = cls(**content)
            if config.name != name:
                log.warning("Config stored in %s is named %s", name, config.name)
                config.name = name

            return config
        else:
            return cls(name=name)

    def save(self):
        """Save the context configuration to a file"""
        content = self.json()
        filename = self.config_file(self.name)
        atomic_write(filename, content)
        return True


class Context(pydantic.BaseModel):
    """Base class for live context instances
    
    The class in the context module  does most of the  heavy lifting
    as the rules are loaded dynamically from disk  and the calculation of 
    dependent data generally relies on the dynamic rules.
    """

    name: str = ''
    config: ContextDefinition = None
    hotwords: dict = {}


def atomic_write(filename, content):
    """Write the content to filename either succeeding or not replacing it"""
    temporary = filename + '~'
    directory = os.path.dirname(filename)
    if not os.path.exists(directory):
        os.makedirs(directory, 0o700)
    with open(temporary, 'w') as fh:
        fh.write(content)
    os.rename(temporary, filename)
    return filename


def write_default_main():
    """Entry point for writing out the default contexts"""
    logging.basicConfig(level=logging.INFO)
    ContextDefinition.write_default_contexts()


class RuleMatch(pydantic.BaseModel):
    """Represents a match made by a rule to a set of words
    
    Note:

        You cannot  linearize a rule match to  json because
        it includes a significant number of cross references 
        back to itself
    """

    class Config:
        # Sigh, settable properties do *not*
        # work nicely with pydantic, as it wants
        # to pre-validate the property before it
        # calls the function
        extra = pydantic.Extra.allow

    rule: Rule = None
    words: List[str] = []
    start_index: int = 0
    stop_index: int = None
    confidence: float = 0.0
    context: Union[None, Context] = None
    # words that matched word placeholders
    var_words: List[str] = []
    # trailing sequence of words that matched phrase placeholder
    var_phrase: Union[None, List[str]] = None
    commit: bool = False

    @property
    def prefix(self):
        return self.words[: self.start_index]

    @property
    def suffix(self):
        return self.words[self.stop_index :]

    @property
    def matched(self):
        return self.words[self.start_index : self.stop_index]

    def set_matched(self, result):
        self.words[self.start_index : self.stop_index] = result


SPECIAL_KEYS = (defaults.WORD_MARKER, defaults.PHRASE_MARKER, None)


def iter_matches(words, rules):
    """Generate all rule-matchings for the given words across all rules"""
    for start in range(len(words)):
        branch = rules
        var_phrase = None
        var_words = []
        i = 0
        for i, word in enumerate(words[start:]):
            if word in branch:
                branch = branch[word]
            elif branch is not rules and defaults.WORD_MARKER in branch:
                branch = branch[defaults.WORD_MARKER]
                var_words.append(word)
            elif branch is not rules and defaults.PHRASE_MARKER in branch:
                branch = branch[defaults.PHRASE_MARKER]
                # IFF rules match the phrase, process the phrase
                var_phrase = words[i:]
                break
            else:
                # we don't match any further rules, do we
                # have a current match?
                i -= 1
                break
        if None in branch:
            rule = branch[None]
            return RuleMatch(
                rule=rule,
                words=words[:],
                start_index=start,
                stop_index=start + i + 1,
                var_words=var_words,
                var_phrase=var_phrase,
            )


def match_rules(words, rules, seen=None, start=0):
    """Find rules which match in the rules"""
    seen = seen or set()

    for start in range(start, len(words)):
        branch = rules
        var_phrase = None
        var_words = []
        i = 0
        for i, word in enumerate(words[start:]):
            if word in branch:
                branch = branch[word]
            elif branch is not rules and defaults.WORD_MARKER in branch:
                branch = branch[defaults.WORD_MARKER]
                var_words.append(word)
            elif branch is not rules and defaults.PHRASE_MARKER in branch:
                branch = branch[defaults.PHRASE_MARKER]
                var_phrase = words[i:]
                # we are pointing at the first word, advance to the last word in phrase...
                i += len(var_phrase) - 1
                break
            else:
                # we don't match any further rules, do we
                # have a current match?
                i -= 1
                break
        if None in branch:  # a rule stops at this point
            rule = branch[None]
            if (i, rule) in seen:
                log.info("Already ran rule %s at %s", rule, i)
                continue
            seen.add((i, rule))
            return RuleMatch(
                rule=rule,
                words=words[start : start + i + 1],
                start_index=start,
                stop_index=start + i + 1,
                var_words=var_words,
                var_phrase=var_phrase,
            )


def compress_no_spaces(working):
    """Compress out no space markers"""
    result = []
    seen = False
    for item in working:
        if item == '^':
            if seen:
                continue
            else:
                seen = True
        else:
            seen = False
        result.append(item)
    return result


def apply_rules(
    transcript,
    rules,
    context=None,
    match_bias=0.25,
    commit=False,
    event=None,
    interpreter=None,
    command_only=False,
):
    """Iteratively apply rules from rule-set until nothing changes"""
    match_set = set()
    working = transcript.words[:]
    # log.info("Working: %s", working)
    for iteration in range(20):
        # log.info("Iteration: %s", iteration)
        matches = 0
        starting = working[:]
        match = match_rules(working, rules, match_set)
        while match and match.stop_index <= len(working):
            matches += 1
            match.transcript = transcript
            match.context = context
            match.commit = commit
            transcript.rule_matches = transcript.rule_matches + [match]

            # log.info("Match: %s", match.words)

            transcript.confidence += match_bias
            rest = working[match.stop_index :]
            # log.info("Remaining: %s", rest)
            try:
                transformed = match.rule(match, interpreter=interpreter, event=event)
                # log.info(
                #     "Transform %s => %s with %s",
                #     working[match.start_index : match.stop_index],
                #     transformed,
                #     match.rule,
                # )
                working[match.start_index : match.stop_index] = transformed
            except StopIteration as err:
                # Immediate return...
                # log.info("Command: %s", working[match.start_index : match.stop_index])
                del working[match.start_index : match.stop_index]

            if rest:
                match = match_rules(
                    working, rules, match_set, start=len(working) - len(rest),
                )
            else:
                # log.info('Reached end')
                match = None
                break
        transcript.confidence += match_bias * matches
        working = compress_no_spaces(working)
        if working == starting:
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


# Forward reference resolutions
Transcript.update_forward_refs()
