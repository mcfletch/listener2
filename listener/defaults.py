"""Constants and shared definitions"""
import os, logging, pwd


def get_username():
    """get the current users user name"""
    return pwd.getpwuid(os.geteuid()).pw_name


HERE = os.path.dirname(os.path.abspath(__file__))
LISTENER_SOURCE = HERE

APP_NAME = 'listener'

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
DEFAULT_DEEPSPEECH_VERSION = '0.7.3'
RELEASE_URL = 'https://github.com/mozilla/DeepSpeech/releases/download/v%(version)s/'
MODEL_FILE = 'deepspeech-%(version)s-models.pbmm'
SCORER_FILE = 'deepspeech-%(version)s-models.scorer'

CACHED_SCORER_FILE = os.path.join(
    MODEL_CACHE, SCORER_FILE % {'version': DEFAULT_DEEPSPEECH_VERSION,}
)


RAW_EVENTS = os.path.join(RUN_DIR, 'events')
FINAL_EVENTS = os.path.join(RUN_DIR, 'clean-events')


DOCKER_CONTAINER = '%s_%s' % (APP_NAME, get_username())
DOCKER_IMAGE = '%s-server' % (APP_NAME,)

SAMPLE_RATE = 16000


def setup_logging(options):
    logging.basicConfig(
        level=logging.DEBUG if options.verbose else logging.WARNING,
        format='%(asctime)s:%(levelname)s:%(name)s:%(lineno)s %(message)s',
    )
