import re, logging, os, json
import pydantic
from . import defaults, ruleloader, models
from . import models, kenlmscorer, commandscorer

log = logging.getLogger(__name__)


class Context(models.Context):
    @classmethod
    def by_name(cls, name):
        """Load the context by name from disk"""
        return cls(name=name, config=models.ContextDefinition.by_name(name),)

    SCORER_CLASSES = {
        'kenlm': kenlmscorer.KenLMScorer,
        'commands': commandscorer.CommandScorer,
    }

    @models.justonce_property
    def loaded_rules(self):
        return ruleloader.load_rules(self.config.rules)

    @property
    def rules(self):
        """Get the rule set for interpretation"""
        return self.loaded_rules[0]

    @property
    def rule_set(self):
        """Get the rule-set for editing purposes"""
        return self.loaded_rules[1]

    @models.justonce_property
    def scorers(self):
        return [
            self.SCORER_CLASSES[scorer.type](definition=scorer, context=self,)
            for scorer in self.config.scorers
            if scorer.type in self.SCORER_CLASSES
        ]

    def score(self, event: models.Utterance, max_count: int = 20):
        """Apply our scorers to the event
        
        Once we have the scorers applied we have a confidence
        ranking for the transcripts, then we want to bias
        based on our context
        """
        estimates = []
        scored_transcripts = []
        for scorer in self.scorers:
            # Show scores and n-gram matches
            log.debug("Score with %s", scorer.definition.name)
            scorer.score(event)
        event.sort()

    def apply_rules(self, event: models.Utterance):
        """Search for key-words in the event transcripts, apply bias to commands
        
        event -- utterance being processed, having already been scored such that
                 we agree to process the first item
        
        """
        rules = self.rules
        for transcript in event.transcripts:
            original = transcript.words[:]
            new_words = models.apply_rules(transcript, rules)
            if new_words != original:
                transcript.words = new_words
                transcript.text = models.words_to_text(new_words)
            break
        return event
