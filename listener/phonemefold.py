# coding: utf-8
from abydos import phonetic
from . import models
from .defaults import LISTENER_SOURCE
import csv, os, itertools
from functools import wraps

PHONEMES = list(
    csv.reader(open(os.path.join(LISTENER_SOURCE, 'phonemes.csv')), delimiter='\t')
)
GRAPHEME_TO_PHONEME = {}
PHONEME_TO_GRAPHEMES = {}


def using_mapping(function):
    @wraps(function)
    def with_mapping(*args, **named):
        build_grapheme_map()
        return function(*args, **named)

    return with_mapping


def build_grapheme_map():
    """Map graphemes to same-phoneme graphemes"""
    if not GRAPHEME_TO_PHONEME:
        print('building map')
        for phoneme, graphemes in PHONEMES:
            graphemes = [x.strip() for x in graphemes.split(',')]
            for grapheme in graphemes:
                GRAPHEME_TO_PHONEME.setdefault(grapheme, set()).add(phoneme)
            PHONEME_TO_GRAPHEMES[phoneme] = set(graphemes)


@using_mapping
def text_to_phonemes(text):
    """Given text, look for sound-alike spellings"""
    found = False
    text = text.strip('-_,. \t\'"')
    if text:
        for graph, phonemes in GRAPHEME_TO_PHONEME.items():
            if text.startswith(graph):
                found = True
                rest = text[len(graph) :].strip()
                if rest:
                    for rest_graph in text_to_phonemes(rest):
                        yield (phonemes,) + rest_graph
                else:
                    yield (phonemes,)
        if not found:
            raise ValueError("Unable to find grapheme spelling for %r", text)
    else:
        yield ()


def possible_spellings(text):
    """Give possible phonetic spellings of text"""
    spellings = set()
    for expansion in text_to_phonemes(text):
        for spelling in all_spellings(expansion):
            spellings.add(spelling)
    return spellings


def phonemes_graphemes(phonemes):
    graphemes = set()
    for phoneme in phonemes:
        graphemes |= PHONEME_TO_GRAPHEMES[phoneme]
    return graphemes


def all_spellings(expansion):
    current, rest = expansion[0], expansion[1:]
    graphemes = phonemes_graphemes(current)
    if graphemes:
        for grapheme in graphemes:
            if not rest:
                yield (grapheme,)
            else:
                for text in all_spellings(rest):
                    yield (grapheme,) + text
    else:
        yield ()


# def test_phoneme_fold():
#     folder = phonetic.NRL()
#     for first, second in [
#         ('two', 'too'),
#         ('to', 'too'),
#         ('ate', 'eight'),
#         ('blue', 'blew'),
#         ('cell', 'cell'),
#         ('wait', 'weight'),
#         # Aren't matched
#         # ('tire', 'tyre'),
#         # ('ail', 'ale'),
#     ]:
#         compressed_1 = folder.encode(first)
#         compressed_2 = folder.encode(second)
#         assert compressed_1 == compressed_2, (compressed_1, compressed_2)
#         # assert False, compressed_1 & compressed_2


def contains_phonetic_spelling(phonetic, test):
    """Does this set of possible phonetics include test-spelling?"""
    for possible in phonetic:
        if len(possible) == len(test):
            found = True
            for p, t in zip(possible, test):
                if not t in p:
                    found = False
            if found:
                return possible
    print("Near matches to", test)
    matches = [x for x in phonetic if test[0] in x[0]]
    for x in matches:
        print(x)
    return None


def test_graphme_map():
    phonetic = list(text_to_phonemes('two'))
    assert contains_phonetic_spelling(phonetic, ['t', 'ʊ'])
    phonetic = list(text_to_phonemes('weight'))
    assert contains_phonetic_spelling(phonetic, ['w', 'e', 'ɪ', 't'])
    phonetic = list(text_to_phonemes('wait'))
    assert contains_phonetic_spelling(phonetic, ['w', 'e', 'ɪ', 't'])


def test_homophones():
    homophones = [
        (('t', 'ʊ'), 'to', 'two', 'too'),
        (('ð', 'eəʳ'), 'there', 'their'),
        (('j', 'ɔ:'), 'your', 'yore'),
        (('b', 'aɪ'), 'by', 'buy', 'bye'),
        (
            ('k', 'ɑ:', 'm', 'p', 'l', 'i:', 'm', 'e', 'n', 't'),
            'compliment',
            'complement',
        ),
    ]
    for wordset in homophones:
        correct, rest = wordset[0], wordset[1:]
        for spelling in rest:
            phonetic = list(text_to_phonemes(spelling))
            assert contains_phonetic_spelling(phonetic, correct), spelling


def test_all_spellings():
    all = possible_spellings('two')
    assert ('t', 'o') in all, all
    assert ('t', 'wo') in all, all
    r = regex(all)
    assert False, r


def regex(all):
    groups = []
    for start, rests in list(first_groups(all)):
        if rests:
            groups.append('%s(%s)' % (start, regex(rests)))
        else:
            groups.append(start)
    return '|'.join(groups)


def first_groups(spellings):
    """Get the grouped components in spellings"""
    for key, spellings in itertools.groupby(spellings, lambda k: k[0]):
        yield key, [spell[1:] for spell in spellings if len(spell) > 1]
