from abydos import phonetic
from . import models
import pydantic


FOLDER = phonetic.NRL()


class BiasingScorer(pydantic.BaseModel):
    """Scores incoming requests as whether they might be commands"""

    commands: dict = {}

    def score(self, event):
        for transcript in event.transcripts:
            text = FOLDER.encode(transcript.text)


def test_phoneme_fold():
    folder = phonetic.NRL()
    for first, second in [
        ('two', 'too'),
        ('to', 'too'),
        ('ate', 'eight'),
        ('blue', 'blew'),
        ('cell', 'cell'),
        ('wait', 'weight'),
        # Aren't matched
        # ('tire', 'tyre'),
        # ('ail', 'ale'),
    ]:
        compressed_1 = folder.encode(first)
        compressed_2 = folder.encode(second)
        assert compressed_1 == compressed_2, (compressed_1, compressed_2)
        # assert False, compressed_1 & compressed_2
