import unittest
from listener import interpreter, ruleloader
from listener.models import (
    Utterance,
    Transcript,
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
            match = interpreter.match_rules(rule.match, rules)
            assert match
            assert match[0].target == rule.target
            result = match[0](*match[1:])
            if match[0].text:
                assert match[0].text in result, (rule.match, rules, result)
            if match[0].no_space_after:
                assert result[-1] == '^', result
            if match[0].no_space_before:
                assert result[0] == '^', result

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
            result = interpreter.words_to_text(
                interpreter.apply_rules(spoken.split(' '), rules)
            )
            assert result == expected, (spoken, result)

    def test_context_loading(self):
        core = interpreter.Context('core')

    def test_junk_utterance_handling(self):
        core = interpreter.Context('core')
        result = core.apply_rules(JUNK_UTTERANCE.copy())
        assert result.transcripts
        assert result.transcripts[0].text == '', 'Did not recognise a junk utterance'


JUNK_UTTERANCE = utt = Utterance(
    partial=False,
    final=True,
    transcripts=[
        Transcript(
            partial=False,
            final=True,
            words=[],
            tokens=[],
            starts=[],
            word_starts=[],
            confidence=1.178935170173645,
        ),
        Transcript(
            partial=False,
            final=True,
            words=['i'],
            tokens=['i'],
            starts=[0.47999998927116394],
            word_starts=[0.47999998927116394],
            confidence=-10.575060844421387,
        ),
        Transcript(
            partial=False,
            final=True,
            words=['a'],
            tokens=['a'],
            starts=[0.47999998927116394],
            word_starts=[0.47999998927116394],
            confidence=-13.048016548156738,
        ),
        Transcript(
            partial=False,
            final=True,
            words=['o'],
            tokens=['o'],
            starts=[0.47999998927116394],
            word_starts=[0.47999998927116394],
            confidence=-13.359726905822754,
        ),
        Transcript(
            partial=False,
            final=True,
            words=['m'],
            tokens=['m'],
            starts=[0.47999998927116394],
            word_starts=[0.47999998927116394],
            confidence=-13.824394226074219,
        ),
        Transcript(
            partial=False,
            final=True,
            words=['h'],
            tokens=['h'],
            starts=[0.47999998927116394],
            word_starts=[0.47999998927116394],
            confidence=-13.980472564697266,
        ),
        Transcript(
            partial=False,
            final=True,
            words=['e'],
            tokens=['e'],
            starts=[0.47999998927116394],
            word_starts=[0.47999998927116394],
            confidence=-14.323654174804688,
        ),
        Transcript(
            partial=False,
            final=True,
            words=['n'],
            tokens=['n'],
            starts=[0.47999998927116394],
            word_starts=[0.47999998927116394],
            confidence=-14.946478843688965,
        ),
        Transcript(
            partial=False,
            final=True,
            words=['d'],
            tokens=['d'],
            starts=[0.47999998927116394],
            word_starts=[0.47999998927116394],
            confidence=-15.496161460876465,
        ),
        Transcript(
            partial=False,
            final=True,
            words=['he'],
            tokens=['h', 'e'],
            starts=[0.47999998927116394, 0.5],
            word_starts=[0.47999998927116394],
            confidence=-15.78717041015625,
        ),
        Transcript(
            partial=False,
            final=True,
            words=['t'],
            tokens=['t'],
            starts=[0.47999998927116394],
            word_starts=[0.47999998927116394],
            confidence=-16.002553939819336,
        ),
        Transcript(
            partial=False,
            final=True,
            words=['f'],
            tokens=['f'],
            starts=[0.47999998927116394],
            word_starts=[0.47999998927116394],
            confidence=-16.987838745117188,
        ),
        Transcript(
            partial=False,
            final=True,
            words=['s'],
            tokens=['s'],
            starts=[0.47999998927116394],
            word_starts=[0.47999998927116394],
            confidence=-17.056884765625,
        ),
        Transcript(
            partial=False,
            final=True,
            words=['g'],
            tokens=['g'],
            starts=[0.47999998927116394],
            word_starts=[0.47999998927116394],
            confidence=-17.59112548828125,
        ),
        Transcript(
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
