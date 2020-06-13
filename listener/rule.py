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
