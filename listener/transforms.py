"""Definitions of rules and targets for user rule-sets"""
from .ruleregistry import named_rule


@named_rule
def title(words):
    return [word.title() for word in words]


@named_rule
def all_caps(words):
    return [word.upper() for word in words]


@named_rule
def constant(words):
    return ['^', '_'.join([x for x in all_caps(words) if x != '^']), '^']


@named_rule
def camel(words):
    result = []
    for word in words:
        result.append(word.title())
        result.append('^')
    if words:
        del result[-1]
    return result


@named_rule
def camel_lower(words):
    return [words[0], '^'] + camel(words[1:])


@named_rule
def underscore_name(words):
    return ['^', '_'.join([x for x in words if x != '^']), '^']


@named_rule
def percent_format(name):
    return ['%(', '^', name, '^', ')s']


@named_rule
def no_spaces(words):
    result = ['^']
    for word in words:
        result.append(word)
        result.append('^')
    return result

@named_rule
def dunder(words):
    """Create a python dunder name"""
    return ['__'] + underscore_name(words) + ['__']
    