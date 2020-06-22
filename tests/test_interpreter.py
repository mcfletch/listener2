import unittest
from listener import (
    interpreter,
    ruleloader,
    context,
    models,
    defaults,
    fuzzymatching,
)


class TestInterpreter(unittest.TestCase):
    def test_loading(self):
        rules, ruleset = ruleloader.load_rules('default')
        assert rules
        assert ruleset
        for rule in ruleset:
            assert rule.match
            assert rule.target

    def test_text_expansion(self):
        rules, ruleset = ruleloader.load_rules('default')
        for rule in ruleset:
            words = rule.match[:]
            if words[-1] == defaults.PHRASE_MARKER:
                words[-1:] = ['moo', 'over', 'there']
            elif words[-1] == defaults.WORD_MARKER:
                words = [(w if w != defaults.WORD_MARKER else 'moo') for w in words]
            match = models.match_rules(words, rules)
            assert match
            assert match.rule == rule
            result = match.rule(match)
            if match.rule.text:
                assert match.rule.text in result.words, result
            if match.rule.no_space_after:
                assert result.words[-1] == '^', result
            if match.rule.no_space_before:
                assert result.words[0] == '^', result

    def test_apply_rules(self):
        rules, ruleset = ruleloader.load_rules('default')
        for spoken, expected in [
            ('close the file period', ' close the file. ',),
            ('open parenthesis this comma that', ' (this, that ',),
            ('no space this', 'this ',),
            ('close bracket no space', ']',),
            ('open triple quote', ' """',),
            ('constant current position', 'CURRENT_POSITION',),
            ('all caps hello there', " HELLO THERE ",),
            ('camel case forgotten dog', ' ForgottenDog ',),
            ('all together there is none', 'thereisnone'),
        ]:
            transcript = models.Transcript(words=spoken.split(' '), confidence=0,)
            words = models.apply_rules(transcript, rules, commit=False)
            assert transcript.confidence > 0, transcript.confidence
            result = models.words_to_text(words)
            assert result == expected, (spoken, result)

    def test_context_loading(self):
        core = interpreter.Context.by_name('english-general')

    def test_junk_utterance_handling(self):
        core = interpreter.Context.by_name('english-general')
        result = core.apply_rules(JUNK_UTTERANCE.copy())
        assert result.transcripts
        assert result.transcripts[0].text == '', 'Did not recognise a junk utterance'

    def test_distance_calculation(self):
        rule = models.Rule(match=['cap-camel', defaults.PHRASE_MARKER])
        distances = fuzzymatching.measure_distance(['caps', 'camel'], rule)
        assert distances[0] == (1, ['caps', 'camel'], ['cap-camel']), distances[0]


JUNK_UTTERANCE = utt = models.Utterance(
    partial=False,
    final=True,
    transcripts=[
        models.Transcript(
            partial=False,
            final=True,
            words=[],
            tokens=[],
            starts=[],
            word_starts=[],
            confidence=1.178935170173645,
        ),
        models.Transcript(
            partial=False,
            final=True,
            words=['i'],
            tokens=['i'],
            starts=[0.47999998927116394],
            word_starts=[0.47999998927116394],
            confidence=-10.575060844421387,
        ),
        models.Transcript(
            partial=False,
            final=True,
            words=['a'],
            tokens=['a'],
            starts=[0.47999998927116394],
            word_starts=[0.47999998927116394],
            confidence=-13.048016548156738,
        ),
        models.Transcript(
            partial=False,
            final=True,
            words=['o'],
            tokens=['o'],
            starts=[0.47999998927116394],
            word_starts=[0.47999998927116394],
            confidence=-13.359726905822754,
        ),
        models.Transcript(
            partial=False,
            final=True,
            words=['m'],
            tokens=['m'],
            starts=[0.47999998927116394],
            word_starts=[0.47999998927116394],
            confidence=-13.824394226074219,
        ),
        models.Transcript(
            partial=False,
            final=True,
            words=['h'],
            tokens=['h'],
            starts=[0.47999998927116394],
            word_starts=[0.47999998927116394],
            confidence=-13.980472564697266,
        ),
        models.Transcript(
            partial=False,
            final=True,
            words=['e'],
            tokens=['e'],
            starts=[0.47999998927116394],
            word_starts=[0.47999998927116394],
            confidence=-14.323654174804688,
        ),
        models.Transcript(
            partial=False,
            final=True,
            words=['n'],
            tokens=['n'],
            starts=[0.47999998927116394],
            word_starts=[0.47999998927116394],
            confidence=-14.946478843688965,
        ),
        models.Transcript(
            partial=False,
            final=True,
            words=['d'],
            tokens=['d'],
            starts=[0.47999998927116394],
            word_starts=[0.47999998927116394],
            confidence=-15.496161460876465,
        ),
        models.Transcript(
            partial=False,
            final=True,
            words=['he'],
            tokens=['h', 'e'],
            starts=[0.47999998927116394, 0.5],
            word_starts=[0.47999998927116394],
            confidence=-15.78717041015625,
        ),
        models.Transcript(
            partial=False,
            final=True,
            words=['t'],
            tokens=['t'],
            starts=[0.47999998927116394],
            word_starts=[0.47999998927116394],
            confidence=-16.002553939819336,
        ),
        models.Transcript(
            partial=False,
            final=True,
            words=['f'],
            tokens=['f'],
            starts=[0.47999998927116394],
            word_starts=[0.47999998927116394],
            confidence=-16.987838745117188,
        ),
        models.Transcript(
            partial=False,
            final=True,
            words=['s'],
            tokens=['s'],
            starts=[0.47999998927116394],
            word_starts=[0.47999998927116394],
            confidence=-17.056884765625,
        ),
        models.Transcript(
            partial=False,
            final=True,
            words=['g'],
            tokens=['g'],
            starts=[0.47999998927116394],
            word_starts=[0.47999998927116394],
            confidence=-17.59112548828125,
        ),
        models.Transcript(
            partial=False,
            final=True,
            words=['r'],
            tokens=['r'],
            starts=[0.47999998927116394],
            word_starts=[0.47999998927116394],
            confidence=-18.298046112060547,
        ),
    ],
)
