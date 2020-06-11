"""provide for the interpretation of incoming utterances based on user provided rules"""
import re, logging, os

log = logging.getLogger(__name__)


def text_entry_rule(match, replace):
    """Create a rule from the text-entry mini-language"""
    no_space_before = replace.startswith('^')
    no_space_after = replace.endswith('^')
    text = bytes(replace.strip('^')[1:-1], 'utf-8').decode('unicode_escape')

    def apply_rule(words, start_index=0, end_index=-1):
        """Given a match on the rule, produce modified result"""
        prefix = words[:start_index]
        suffix = words[end_index:]
        result = []
        if no_space_before:
            result.append('^')
        result.append(text)
        if no_space_after:
            result.append('^')
        return prefix + result + suffix

    apply_rule.__name__ = 'text_entry_%s' % ("_".join(match))
    apply_rule.match = match
    apply_rule.text = text
    apply_rule.replace = replace
    apply_rule.no_space_after = no_space_after
    apply_rule.no_space_before = no_space_before
    return apply_rule


def transform_rule(match, transformation):
    phrase = match[-1] == PHRASE_MARKER
    word = match[-1] == WORD_MARKER

    def apply_rule(words, start_index=0, end_index=-1):
        """Given a match, transform and return the results"""
        working = words[:]
        if phrase:
            working[start_index:] = transformation(words[end_index - 1 :])
        else:
            working[start_index:end_index] = transformation(
                words[end_index - 1 : end_index]
            )
        return working

    apply_rule.__name__ = 'transform_entry_%s' % ("_".join(match))
    apply_rule.match = match
    apply_rule.text = None
    return apply_rule


# General commands that already recognise well
good_commands = '''
# Typing characters
new line => ^'\\n'^
new paragraph => ^'\\n'^
tab key => ^'\\t'^
period => ^'.'
dot => ^'.'^
question mark => ^'?'
exclamation mark => ^'!'
open parentheses => '('^
open parenthesis => '('^
close parentheses => ^')'
close parenthesis => ^')'
underscore => ^'_'^
open bracket => '['^
close bracket => ^']'
open quote => '"'^
close quote => ^'"'
quote quote => '""'
open single quote => "'"^
close single quote => ^"'"
open triple quote => '"""'^
close triple quote => ^'"""'
triple start quote => '"""'^
triple end quote => ^'"""'
ampersand character => "&"
and character => '&'
and symbol => '&'
or symbol => '|'
or character => '|'
pipe character => "|"
backslash => ^'\\\\'^
slash => ^'/'^
slash slash => ^'//'
space => ^' '^
bang => ^'!'
sharp symbol => ^'#'
hash symbol => ^'#'
at symbol => ^'@'^
no space => ^''^
comma => ^','
colon => ^':'^
semi colon => ^';'
equals => '='
equal sign => '='
not equal => '!='
double equal => '=='
double equals => '=='
dollar sign => ^'$'^
per cent format ${name} => percent_format()
percent format ${name} => percent_format()
per cent => ^'%'^
asterisk => ^'*'^
asterisk character => '*'^ 
asterisk asterisk  => '**'^
plus character => '+'
minus character => '-'
hyphen => ^'-'^
division character => '/'
greater than => '>'
less than => '<'
ellipsis => ^'...'
caret => ^'^'^ 
caret symbol  => ^'^'^ 
caret character => ^'^'^ 
arrow symbol => '=>'
back tick => '`'
open brace => ^'{'^
close brace => ^'}'^
tilde => '~'^

all caps ${phrase}  => all_caps()
all cap ${phrase}  => all_caps()
title ${phrase} => title()
cap ${word} => title()
caps ${word} => title()
capital ${word} => title()
constant ${phrase} => constant()
camel case ${phrase} => camel()
camel caps ${phrase} => camel()
see name ${phrase} => camel_lower()
underscore name ${phrase} => underscore_name()
under name ${phrase} => underscore_name()


# # Key symbol entry
# press enter => \\key (Enter)
# go up => \\key (Up)
# go down => \\key (Down)
# go left => \\key (Left)
# go right => \\key (Right)
# go home => \\key (Home)
# go end => \\key (End)
# indent => \\key (Tab)
# reduce indent => \\key (Shift+Tab)
# unselect => \\key (Escape)
# escape => \\key (Escape)
# alt ${word} => \\key (Alt+${word})
 
# caps on => caps_on()
# caps off => caps_off()
# spell that => correction()
# type that => correction()
# spell out => spell_on()
# stop spell => spell_off()
# spell stop =>  spell_off()
# camel case => camel_on()
# dunder ${phrase} => '_'^'_'^${phrase}^'_'^'_'

# start listening => start()
# wake up => start()
# stop listening => stop()
# go to sleep => stop()
# undo that => undo()
# correct that => correction()
# scratch that => undo()
# select left => \\key (Shift+Ctrl+Left)
# select right => \\key (Sift+Ctrl+Left)
# select ${number} words => \\key (Shift+Ctrl+Right)
# select back ${number} words => \\key (Shift+Ctrl+Right)
# select up line => \\key (Shift+Up)
# select down line => \\key (Shift+Down)
'''
# General commands that don't recognise well
BAD_COMMANDS = """
press tab
dedent
comma
backspace
word left
word right
line start 
line end
octothorpe => ^'#'
shebang => ^'#!'
"""

DICTATION_RULES  =  

NAMED_RULES = {}


def named_rule(function):
    NAMED_RULES[function.__name__] = function
    return function


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
        result.append(word)
        result.append('^')
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


def iter_rules(command_set):
    for i, line in enumerate(command_set.splitlines()):
        line = line.strip()
        if (not line) or line.startswith('#'):
            continue
        try:
            pattern, target = line.split('=>', 1)
        except ValueError as err:
            log.warning("Unable to parse rule #%i: %r", i + 1, line)
            continue
        pattern = pattern.strip().split()
        target = target.strip()
        yield pattern, target


def load_rules(command_set, rules=None):
    """load a set of commands from a string"""
    rules = rules or {}
    for pattern, target in iter_rules(command_set):
        branch = rules
        for word in pattern:
            branch = branch.setdefault(word, {})
        if target.endswith('()'):
            rule = transform_rule(pattern, NAMED_RULES[target[:-2]])
        else:
            rule = text_entry_rule(pattern, target)
        branch[None] = rule
    return rules


# class Context(attr.s):
#     """A chaining store of context based on communication environment"""
#     parent: 'Context' = None
#     rules: 'List[RuleSet]' = None
#     history: 'List[Utterance]' = None

#     def interpret(self, event):
#         """Attempt to determine what this event likely means"""

PHRASE_MARKER = '${phrase}'
WORD_MARKER = '${word}'


def match_rules(words, rules):
    """Find rules which match in the rules"""
    for start in range(len(words)):
        branch = rules
        i = 0
        for i, word in enumerate(words[start:]):
            if word in branch:
                branch = branch[word]
            elif WORD_MARKER in branch:
                branch = branch[WORD_MARKER]
            elif PHRASE_MARKER in branch:
                branch = branch[PHRASE_MARKER]
                break
            else:
                # we don't match any further rules, do we
                # have a current match?
                i -= 1
                break
        if None in branch:
            rule = branch[None]
            return rule, words, start, start + i + 1


def apply_rules(words, rules):
    """Iteratively apply rules from rule-set until nothing changes"""
    working = words[:]
    for i in range(20):
        match = match_rules(working, rules)
        if match:
            working = match[0](*match[1:])
        else:
            break
    return working


def words_to_text(words):
    """Compress words taking no-space markers into effect..."""
    result = []
    no_space = False
    for item in words:
        if item == '^':
            no_space = True
        else:
            if not no_space:
                result.append(' ')
            result.append(item)
            no_space = False
    if not no_space:
        result.append(' ')
    return ''.join(result)


EVENTS = '/run/user/%s/recogpipe/events' % (os.geteuid())
LIVE_EVENTS = '/run/user/%s/recogpipe/clean-events' % (os.geteuid())


def main():
    logging.basicConfig(level=logging.DEBUG)
    from . import eventreceiver, eventserver
    import json

    rules = load_rules(good_commands)
    queue = eventserver.create_sending_threads(LIVE_EVENTS)
    for event in eventreceiver.read_from_socket(sockname=EVENTS, connect_backoff=2.0,):
        if event.get('final'):
            for transcript in event['transcripts']:
                new_words = apply_rules(transcript['words'], rules)
                transcript['text'] = words_to_text(new_words)
                transcript['words'] = new_words
                break
            queue.put(event)
