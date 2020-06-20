import pydantic
from . import models


class KenLMScorer(pydantic.BaseModel):
    """Score based on a KenLM model as in upsteam DeepSpeech"""

    definition: models.ScorerDefinition = None

    _scorer = None

    @property
    def name(self):
        return self.definition.name

    @models.justonce_property
    def scorer(self):
        """Load our scorer model (a KenLM model by default)"""
        # NOTE: we do *not* import this at the top level of
        # the module so that the plugin can be loaded without
        # loading up the dependency
        import kenlm

        model = kenlm.Model(self.definition.language_model)
        return model

    def score(self, utterance: models.Utterance):
        """Score the utterance"""
        scorer = self.scorer
        scores = []
        for transcript in utterance.transcripts:
            score = scorer.score(transcript.text)
            scores.append((score, transcript))
        return sorted(scores, key=lambda x: x[0], reverse=True)
