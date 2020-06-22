import unittest, logging
from listener import (
    interpreter,
    ruleloader,
    context,
    models,
    defaults,
    fuzzymatching,
)

log = logging.getLogger(__name__)


def has_rule(match, rules):
    for rule in rules:
        if rule.match == match:
            return rule
    return None


class TestInterpreter(unittest.TestCase):
    def test_fuzzy_matching(self):
        rules, ruleset = ruleloader.load_rules('code')
        table = fuzzymatching.fuzzy_lookup_table(ruleset)
        for misspelling, match in [
            ('cloes quote', 'close quote'),
            ('open brin', 'open paren'),
            ('knew paragraph', 'new paragraph'),
            ('opened paren', 'open paren'),
            # ('hoping paren', 'open paren'),
        ]:
            rules, meta = fuzzymatching.fuzzy_lookup(list(misspelling), table)
            if not rules:
                assert False, (
                    fuzzymatching.metaphone(misspelling),
                    fuzzymatching.metaphone(match),
                )
            assert rules, (misspelling, match)
            rule = has_rule(match.split(), rules)
            assert rule, (misspelling, match, rules)
            if len(rules) > 1:
                log.warning(
                    "More than one rule matched: %s (%s)",
                    misspelling,
                    [rule.match for rule in rules],
                )
                assert False

    # def test_distance_calculation(self):
    #     rule = models.Rule(match=['cap-camel', defaults.PHRASE_MARKER])
    #     distances = fuzzymatching.measure_distance(['caps', 'camel'], rule)
    #     assert distances[0] == (1, ['caps', 'camel'], ['cap-camel']), distances[0]

