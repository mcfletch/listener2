"""provide for the interpretation of incoming utterances based on user provided rules"""
import re, logging 
log = logging.getLogger(__name__)

def text_entry_rule(match, replace):
    """Create a rule from the text-entry mini-language"""
    no_space_before = replace.startswith('^')
    no_space_after = replace.endswith('^')
    text = replace.strip('^')[1:-1]
    def apply_rule(words, start_index=0,end_index=-1):
        """Given a match on the rule, produce modified result"""
        prefix = words[:start_index]
        suffix = words[end_index:]
        result = []
        if no_space_before:
            result.append('^')
        result.append(text)
        if no_space_after:
            replace.append('^')
        return prefix + result + suffix
    apply_rule.__name__ = 'text_entry_%s'%("_".join(match))
    apply_rule.match = match 
    apply_rule.replace = replace
    apply_rule.no_space_after = no_space_after
    apply_rule.no_space_before = no_space_before

    return apply_rule

# General commands that already recognise well
good_commands = """
# Typing characters
# new line => ^'\\n'
# new paragraph => ^'\\n'
period => ^'.'
question mark => ^'?'
exclamation mark => ^'!'
open parentheses => '('^
close parentheses => ^')'
underscore => ^'_'^
open bracket => '['^
close bracket => ^']'
open quote => '"'^
close quote => ^'"'
open single quote => "'"^
close single quote => ^"'"
ampersand character => "&"
pipe character => "|"
backslash => ^'\\'^
slash => ^'/'^
space => ^' '^
bang => ^'!'
at symbol => ^'@'^
no space => ^''^

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

# all caps on  => all_caps_start()
# all caps off => all_caps_stop()
# caps on => caps_on()
# caps off => caps_off()
# spell that => correction()
# type that => correction()
# cap ${word} => title(${word})
# caps ${word} => title(${word})
# capital ${word} => title(${word})
# spell out => spell_on()
# stop spell => spell_off()
# spell stop =>  spell_off()
# camel case => camel_on()
# constant ${phrase} => camel_on() ${phrase} camel_off()
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
"""
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
asterisk => '*' 
octothorpe => ^'#'
shebang => ^'#!'
"""

def iter_rules(command_set):
    for i,line in enumerate(command_set.splitlines()):
        line = line.strip()
        if (not line) or line.startswith('#'):
            continue 
        try:
            pattern,target = line.split('=>',1)
        except ValueError as err:
            log.warning("Unable to parse rule #%i: %r", i+1, line)
            import pdb;pdb.set_trace()
            continue
        pattern = pattern.strip().split()
        target = target.strip()
        yield pattern, target

def load_commands(command_set,rules=None):
    """load a set of commands from a string"""
    rules = rules or {}
    for pattern,target in iter_rules(command_set):
        branch = rules
        for word in pattern:
            branch = branch.setdefault(word,{})
        branch[None] = text_entry_rule(pattern,target)
    return rules

# class Context(attr.s):
#     """A chaining store of context based on communication environment"""
#     parent: 'Context' = None
#     rules: 'List[RuleSet]' = None
#     history: 'List[Utterance]' = None 

#     def interpret(self, event):
#         """Attempt to determine what this event likely means"""

def match_rules(words,rules):
    """Find rules which match in the rules"""
    for start in range(len(words)):
        # log.info("Start at %s", words[start:])
        branch = rules
        for i,word in enumerate(words[start:]):
            if word in branch:
                # log.info("%s in branch", word)
                branch = branch[word]
            else:
                # we don't match any further rules, do we 
                # have a current match?
                break
        if None in branch:
            # log.info("Have none in branch")
            return branch[None],words,start,start+i
