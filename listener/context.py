import re, logging, os, json
import pydantic
from . import defaults, ruleloader, models
from . import models, kenlmscorer

log = logging.getLogger(__name__)


class Context(object):
    def __init__(self, name):
        self.name = name
        self.config = models.ContextDefinition.by_name(self.name)

    SCORER_CLASSES = {
        'kenlm': kenlmscorer.KenLMScorer,
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
            ratings = scorer.score(event)[:10]
            if ratings and ratings[0][1].text != '':  # only log non-empty scored values
                log.info("With the %s scorer", scorer.name)
                for rating, transcript in ratings:
                    log.info("%8s => %r", '%0.2f' % (rating), transcript.text)
        return sorted(estimates)

    def apply_rules(self, event):
        rules = self.rules
        for transcript in event.transcripts:
            original = transcript.words[:]
            new_words = models.apply_rules(transcript.words, rules)
            if new_words != original:
                transcript.text = models.words_to_text(new_words)
                transcript.words = new_words
            log.debug("%r => %r", models.words_to_text(original), transcript.text)
            break
        return event
