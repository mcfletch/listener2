"""Fuzzy matching of rules (too inefficient to use)"""
import pydantic, os, logging, json
from typing import List, Optional, Callable, Dict
from doublemetaphone import doublemetaphone as metaphone
from .models import Rule, SPECIAL_KEYS
from .defaults import PHRASE_MARKER, WORD_MARKER


def fuzzy_lookup_table(rule_set):
    """Given a set of rules try to create a metaphone'd lookup table"""
    lookup_table = {}
    for rule in rule_set:
        match = []
        for word in rule.match:
            if word not in SPECIAL_KEYS:
                match.append(word)
        prefix = "".join(match)
        prefix = metaphone(prefix)
        for character in prefix:
            sub_table = lookup_table.setdefault(character, {})
            table = sub_table
        if rule.match[-1] in SPECIAL_KEYS:
            table.setdefault(rule.match[-1], []).append(rule)
        else:
            table.setdefault(None, []).append(rule)
    return lookup_table


def fuzzy_lookup(tokens, rule_set):
    """Do a fuzzy lookup on tokens to find matching rules"""
    # we'll have to de-metaphone these to decide what part of
    # the phrase needs to be passed on...
    phonetic = metaphone(''.join(tokens))
    for start in range(len(phonetic)):
        table = rule_set
        for offset, char in enumerate(phonetic[start:]):
            if char in table:
                table = table[char]
            elif table is not rule_set:
                if PHRASE_MARKER in table:
                    return table[PHRASE_MARKER], phonetic[start:]
                if WORD_MARKER in table:
                    return table[WORD_MARKER], phonetic[start:]
                elif None in table:
                    return table[None], phonetic[start : start + offset]
    return [], ''


# def fuzzy_match_branch(word, branch, max_distance=0, distance_calc=None):
#     """return match,new_branch for word in branch"""
#     value = branch.get(word)
#     if value is not None:
#         yield 0, value
#     if max_distance and distance_calc:
#         for key, new_branch in branch.items():
#             if key in SPECIAL_KEYS:
#                 continue
#             elif key == word:
#                 continue
#             distance = distance_calc(key, word)
#             if distance < max_distance:
#                 yield distance, new_branch


# def measure_distance(words: List[str], rule: Rule, distance_calc=levenshtein_distance):
#     """Measure distance from rule-match at words

#     returns sorted [(distance,[match,words],[rule,words]),...]
#     """
#     rule_prefix = []
#     for test in rule.match:
#         if test not in SPECIAL_KEYS:
#             rule_prefix.append(test)
#     rule_string = (' '.join(rule_prefix)).replace('-', ' ')
#     distances = []
#     for subset in (
#         words[: len(rule_prefix)],
#         words[: len(rule_prefix) - 1],
#         words[: len(rule_prefix) + 1],
#     ):
#         test = ' '.join([word.replace('-', ' ') for word in subset])
#         distances.append((distance_calc(rule_string, test), subset, rule_prefix))
#     return sorted(distances)


# def fuzzy_match_rules(words, rules, max_distance=2, distance_calc=levenshtein_distance):
#     """Find rules which loosely match in the rules"""
#     from . import ruleloader

#     for i, start in enumerate(words):

#         for rule in rules:
#             distance = distance_calc(rule.match[0], start)
#             if distance < max_distance:
#                 for distance, subset, rulesub in measure_distance(
#                     words[i:], rule, distance_calc=distance_calc
#                 ):
#                     if distance < max_distance:
#                         yield RuleMatch(
#                             confidence=-distance,
#                             rule=rule,
#                             words=words[:i] + rulesub + words[i + len(subset) :],
#                             start_index=i,
#                             stop_index=i + len(subset),
#                         )
