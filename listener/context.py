import re, logging, os, json
import pydantic, typing
from . import defaults, ruleloader, models
from . import kenlmscorer, commandscorer

log = logging.getLogger(__name__)


class Context(models.Context):
    """And interpretation context for our interpreter
    
    Binds together the various bits which define how
    the interpreter will weight given interpretations of 
    the  user's utterances.
    """

    @classmethod
    def by_name(cls, name: str):
        """Load the context by name from disk"""
        return cls(name=name, config=models.ContextDefinition.by_name(name),)

    SCORER_CLASSES = {
        'kenlm': kenlmscorer.KenLMScorer,
        'commands': commandscorer.CommandScorer,
    }

    @models.justonce_property
    def loaded_rules(self):
        """Load the rules from disk and compile them into a matching table"""
        log.info("Loading rules for context %r from %r", self.name, self.config.rules)
        return ruleloader.load_rules(self.config.rules)

    @models.justonce_property
    def boosts(self):
        """Calculate the initial boosts values from our rules"""
        initial = {}
        rules = self.rule_set
        for rule in rules:
            for boost_word, boost in rule.boost_words():
                initial[boost_word] = max((initial.get(boost_word, 0), boost))
        return initial

    def add_hotwords(self, boosts: typing.Dict[str, float]):
        """Add to the boosts for hotwords on context scoring"""
        self.hotwords.update(boosts)
        return self.hotwords

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
        """ Create our scoring models based on our definition"""
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

        for transcript in event.transcripts:
            boost = 0
            for word in transcript.words:
                for boosts in (self.boosts, self.hotwords):
                    boost += boosts.get(word, 0)
            if boost:
                log.debug('Boosting confidence on %s by %s', transcript.words, boost)
            transcript.confidence += boost

        event.sort()

    def apply_hotwords(self, event: models.Utterance, max_count: int = 20):
        """Apply simple boost based on matching hot words"""

    def apply_rules(self, event: models.Utterance, interpreter=None):
        """Search for key-words in the event transcripts, apply bias to commands
        
        event -- utterance being processed, having already been scored such that
                 we agree to process the first item
        
        """
        rules = self.rules
        for transcript in event.transcripts[:5]:
            original = transcript.words[:]
            new_words = models.apply_rules(
                transcript,
                rules,
                interpreter=interpreter,
                event=event,
                context=self,
                command_only=self.name == defaults.STOPPED_CONTEXT,
            )
            if new_words != original:
                transcript.words = new_words
                transcript.text = models.words_to_text(new_words)

        return event
