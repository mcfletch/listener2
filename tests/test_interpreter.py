import unittest
from recogpipe import interpreter

class TestInterpreter(unittest.TestCase):
    def test_text_expansion(self):
        rules = interpreter.load_commands(
            interpreter.good_commands,
        )
        assert rules
        for pattern,replace in interpreter.iter_rules(interpreter.good_commands):
            match = interpreter.match_rules(pattern,rules)
            assert match 
            assert match[0].replace == replace
