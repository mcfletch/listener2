import logging
from os import name
from ..ruleregistry import named_rule
from .. import defaults

log = logging.getLogger(__name__)


@named_rule
def stop_listening(words, interpreter):
    """Tell  the interpreter to stop processing input"""
    interpreter.stop_listening()
    raise StopIteration('Reached a command operation')


@named_rule
def start_listening(words, interpreter):
    """Tell the interpreter to resume processing input"""
    interpreter.start_listening()
    raise StopIteration('Reached a command operation')


@named_rule
def set_context(words, interpreter):
    """Tell the interpreter to switch to a specific input processing context"""
    interpreter.set_context(words[0])
    raise StopIteration('Reached a command operation')


@named_rule
def restore_context(words, interpreter):
    """Restore previously-set context"""
    interpreter.restore_context()
    raise StopIteration('Reached a command operation')


@named_rule
def start_spelling(words, interpreter):
    """Switch to the spelling context in the interpreter"""
    interpreter.set_context(defaults.SPELLING_CONTEXT)
    raise StopIteration('Reached a command operation')
