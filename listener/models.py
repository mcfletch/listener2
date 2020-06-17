"""Data-model class for a rule"""
import pydantic, os, logging, json
from typing import List, Optional, Callable, Dict
from . import defaults

log = logging.getLogger(__name__)

KENLM = 'kenlm'


def null_transform(words, start_index=0, end_index=0):
    """Used when the user references an unknown transformation
    
    Always returns the incoming content without modification
    """
    return words


class Rule(pydantic.BaseModel):
    """Represents a single (user defined) rule for interpreting dictation"""

    match: List[str] = []
    target: str = ''  # textual definition of the target
    text: Optional[str]
    no_space_after: bool = False
    no_space_before: bool = False
    caps_after: bool = False
    process: List[Callable] = [null_transform]
    source: str = ''

    def format(self):
        """Format as content for a textual rules-file"""
        return '%s: %s => %s' % (self.source, ' '.join(self.match), self.target)

    def __str__(self):
        return self.format()

    def __call__(self, *args, **named):
        """Call our processing function"""
        try:
            return self.process[0](*args, **named)
        except Exception as err:
            err.args += (self,)
            raise


class Transcript(pydantic.BaseModel):
    """Represents a potential transcript for an utterance"""

    partial: bool = False
    final: bool = True
    text: str = ''  # debugging text
    words: List[str] = []
    tokens: List[str] = []  # tokens predicted by backend
    starts: List[float] = []  # relative starts of tokens
    words: List[str] = []  # space-separated blocks
    word_starts: List[float] = []  # start of each space-separated block
    confidence: float = 0.0  # estimate of confidence for the whole transcript...


class Utterance(pydantic.BaseModel):
    """Represents a single utterance detected by the backend"""

    utterance_number: int = 0
    partial: bool = False
    final: bool = True
    transcripts: List[Transcript] = []


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
    """Defines a scorer for a particular context"""

    type: str = KENLM
    name: str = 'default'
    language_model: str = defaults.CACHED_SCORER_FILE

    @classmethod
    def by_name(cls, name):
        name = os.path.basename(name)
        for path in [defaults.MODEL_CACHE]:  # some shared storage too
            filename = os.path.join(path, '%s.scorer' % (name))
            if os.path.exists(filename):
                return cls(name=name, language_model=filename, type=KENLM,)
        raise ValueError("Uknown scorer: %s" % (name,))


class ContextDefinition(pydantic.BaseModel):
    """A biasing  context which modifies the of a particular transcription

    """

    name: str = ''
    scorers: List[str] = []
    rules: str = 'default'

    @classmethod
    def context_names(cls):
        """Return the ContextDefinitions for all contexts known"""
        seen = set()
        for directory in [
            defaults.CONTEXT_DIR,
            defaults.BUILTIN_CONTEXTS,
        ]:
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
            result.append(cls.load_config(name=name))
        return result

    @classmethod
    def write_default_contexts(cls):
        code = ContextDefinition(
            name='code', scorers=[ScorerDefinition.by_name('code')], rules='code',
        )

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
    def load_config(cls, name):
        """Load configuration from the named file"""
        filename = cls.config_file(name)
        if os.path.exists(filename):
            config = cls(**json.loads(open(filename).read()))
            if config.name != name:
                log.warning("Config stored in %s is named %s", name, config.name)
                config.name = name

            return config
        else:
            return cls(name=name)

    def save_config(self):
        """Save the context configuration to a file"""
        content = self.json()
        filename = self.config_file(self.name)
        atomic_write(filename, content)
        return True


def atomic_write(filename, content):
    """Write the content to filename either succeeding or not replacing it"""
    temporary = filename + '~'
    with open(temporary, 'w') as fh:
        fh.write(content)
    os.rename(temporary, filename)
    return filename
