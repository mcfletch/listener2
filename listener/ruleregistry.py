"""Rule registration"""

NAMED_RULES = {}


def named_rule(function):
    """Mark a function as a named rule for use in user rule-sets
    
    Decorator that allows the function to be referenced from
    your rule sets.

    @named_rule
    def no_space(words):
        return ''.join([word for word in words if word != '^'])

    all togther => ^no_space()^
    """
    NAMED_RULES[function.__name__] = function
    return function


def rule_by_name(name):
    """Lookup a named rule"""
    return NAMED_RULES.get(name)
