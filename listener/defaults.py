"""Constants and shared definitions"""
import os, logging, pwd
from functools import wraps


def get_username():
    """get the current users user name"""
    return pwd.getpwuid(os.geteuid()).pw_name


HERE = os.path.dirname(os.path.abspath(__file__))
LISTENER_SOURCE = HERE

APP_NAME = 'listener'
APP_NAME_HUMAN = 'Listener Voice Dictation'
APP_NAME_SHORT = 'Listener'

USER_RUN_DIR = os.environ.get('XDG_RUNTIME_DIR', '/run/user/%s' % (os.geteuid()))
USER_CACHE_DIR = os.environ.get('XDG_CACHE_HOME', os.path.expanduser('~/.cache'))


RUN_DIR = os.path.join(USER_RUN_DIR, APP_NAME)
DEFAULT_INPUT = os.path.join(RUN_DIR, 'audio')
DEFAULT_OUTPUT = os.path.join(RUN_DIR, 'events')

USER_CONFIG_DIR = os.environ.get('XDG_CONFIG_DIR', os.path.expanduser('~/.config/'))
CONFIG_DIR = os.path.join(USER_CONFIG_DIR, APP_NAME)
CONTEXT_DIR = os.path.join(CONFIG_DIR, 'contexts')

CACHE_DIR = os.path.join(USER_CACHE_DIR, APP_NAME)
MODEL_CACHE = os.path.join(CACHE_DIR, 'model')
DEFAULT_DEEPSPEECH_VERSION = '0.9.3'
RELEASE_URL = 'https://github.com/mozilla/DeepSpeech/releases/download/v%(version)s/'
MODEL_FILE = 'deepspeech-%(version)s-models.pbmm'
SCORER_FILE = 'deepspeech-%(version)s-models.scorer'

CACHED_SCORER_FILE = os.path.join(
    MODEL_CACHE, SCORER_FILE % {'version': DEFAULT_DEEPSPEECH_VERSION,}
)

RAW_EVENTS = os.path.join(RUN_DIR, 'events')
FINAL_EVENTS = os.path.join(RUN_DIR, 'clean-events')

BUILTIN_RULESETS = os.path.join(LISTENER_SOURCE, 'rulesets')
BUILTIN_CONTEXTS = os.path.join(LISTENER_SOURCE, 'contexts')

DOCKER_CONTAINER = '%s_%s' % (APP_NAME, get_username())
DOCKER_IMAGE = '%s-server' % (APP_NAME,)

SAMPLE_RATE = 16000

PHRASE_MARKER = '${phrase}'
WORD_MARKER = '${word}'

DBUS_NAME = 'com.vrplumber.Listener'
DBUS_INTERPRETER_PATH = '/Interpreter'
DBUS_SERVICE_PATH = '/Service'

PARTIAL_RESULT_EVENT = '%s.PartialResult' % (DBUS_NAME,)
FINAL_RESULT_EVENT = '%s.FinalResult' % (DBUS_NAME,)

MICROPHONE_PREFERENCE_KEY = 'audioview.microphone'
MICROPHONE_VOLUME_KEY = 'audioview.volume'
MICROPHONE_ENABLED_KEY = 'audioview.enable_audio'

DEFAULT_CONTEXT = 'english-python'
STOPPED_CONTEXT = 'english-stopped'
SPELLING_CONTEXT = 'english-spelling'


def setup_logging(options, filename=None):
    logging.basicConfig(
        level=logging.DEBUG if options.verbose else logging.WARNING,
        format='%(asctime)s:%(levelname)7s:%(name)30s:%(lineno)4s %(message)s',
        filename=os.path.join(RUN_DIR, filename) if filename else None,
    )


def log_on_fail(log):
    """Decorator to log failures to the given log on function failure"""

    def wrapper(function):
        @wraps(function)
        def with_log_on_fail(*args, **named):
            try:
                return function(*args, **named)
            except Exception as err:
                log.exception(
                    'Failure on %s with *%s **%s', function.__name__, args, named
                )
                raise

        return with_log_on_fail

    return wrapper

