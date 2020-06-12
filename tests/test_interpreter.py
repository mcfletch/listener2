import unittest
from listener import interpreter


class TestInterpreter(unittest.TestCase):
    def test_loading(self):
        rules, ruleset = interpreter.load_rules('default')
        assert rules
        assert ruleset
        for rule in ruleset:
            assert rule.match
            assert rule.target

    def test_text_expansion(self):
        rules, ruleset = interpreter.load_rules('default')
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
        rules, ruleset = interpreter.load_rules('default')
        for spoken, expected in [
            ('close the file period', ' close the file. ',),
            ('open parenthesis this comma that', ' (this, that ',),
            ('no space this', 'this ',),
            ('close bracket no space', ']',),
            ('open triple quote', ' """',),
            ('constant current position', 'CURRENT_POSITION',),
            ('all caps hello there', " HELLO THERE ",),
            ('camel case forgotten dog', ' ForgottenDog ',),
        ]:
            result = interpreter.words_to_text(
                interpreter.apply_rules(spoken.split(' '), rules)
            )
            assert result == expected, (spoken, result)
