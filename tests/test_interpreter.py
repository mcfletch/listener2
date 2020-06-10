import unittest
from recogpipe import interpreter

class TestInterpreter(unittest.TestCase):
    def test_text_expansion(self):
        rules = interpreter.load_rules(
            interpreter.good_commands,
        )
        assert rules
        for pattern,replace in interpreter.iter_rules(interpreter.good_commands):
            match = interpreter.match_rules(pattern,rules)
            assert match 
            assert match[0].replace == replace
            result = match[0](*match[1:])
            assert match[0].text in result, (pattern, rules, result )
            if match[0].no_space_after:
                assert result[-1] == '^', result 
            if match[0].no_space_before:
                assert result[0] == '^', result 
    def test_apply_rules(self):
        rules = interpreter.load_rules(
            interpreter.good_commands,
        )
        for spoken,expected in [
            (
                'close the file period',
                ' close the file. ',
            ),
            (
                'open parenthesis this comma that',
                ' (this, that ',
            ),
            (
                'no space this',
                'this ',
            ),
            (
                'close bracket no space',
                ']',
            ),
            (
                'open triple quote',
                ' """',
            ),
            (
                'constant current position',
                'CURRENT_POSITION',
            ),
            (
                'all caps hello there',
                " HELLO THERE ",
            ),
            (
                'camel case forgotten dog',
                'ForgottenDog',
            ),

        ]:
            result = interpreter.words_to_text(
                interpreter.apply_rules(spoken.split(' '),rules)
            )
            assert result == expected, (spoken,result)
