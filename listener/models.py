"""Data-model class for a rule"""
import pydantic
from typing import List, Optional, Callable


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
