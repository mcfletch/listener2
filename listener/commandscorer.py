"""Attempt to provide contextual biasing based on current command dictionary"""
import pydantic
import logging
from . import models

log = logging.getLogger(__name__)


class CommandScorer(pydantic.BaseModel):
    """Score incoming commands based on command/vocabulary-matching
    
    Given a set of N target things that might be
    in the middle of an utterance, update score based
    on the edit-distance factor to having targets
    recognised
    """

    command_bias: float = 5.0  # log probability, so 1 => 10x more likely to match...
    definition: models.ScorerDefinition = None
    context: models.Context = None

    @property
    def name(self):
        return self.definition.name

    def score(self, utterance: models.Utterance):
        """Score the utterance (adds to base confidence if matches a command)"""
        log.info("Applying command score with %s rules", len(self.context.rules))
        for transcript in utterance.transcripts:
            if transcript.confidence > -30:
                log.debug(
                    '% 8s %s', '%0.1f' % (transcript.confidence), transcript.tokens,
                )
        for transcript in utterance.transcripts:
            match = models.match_rules(transcript.words, self.context.rules)
            if match:
                transcript.confidence += self.command_bias
                log.info("Adding to score of %s", transcript.words)
        return utterance
