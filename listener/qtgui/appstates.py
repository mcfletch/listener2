"""App-specific icons"""
from .. import models, defaults

APP_STATES = [
    models.AppState(
        key='stopped',
        icon='panel-icon-stopped',
        text='Stopped',
        tooltip='%s is not currently processing audio at all'
        % (defaults.APP_NAME_SHORT),
    ),
    models.AppState(
        key='stop-listening',
        icon='panel-icon-paused',
        text='Not Listening',
        tooltip='%s is not listening/dictating but is processing audio waiting for "start listening"'
        % (defaults.APP_NAME_SHORT,),
    ),
    models.AppState(
        key='start-listening',
        icon='panel-icon-recording',
        text='Listening',
        tooltip='%s is listening/dictating' % (defaults.APP_NAME_SHORT,),
    ),
    models.AppState(
        key='error',
        icon='panel-icon-error',
        text='Error!',
        tooltip='%s cannot listen due to an error' % (defaults.APP_NAME_SHORT,),
    ),
]
APP_STATE_MAP = dict([(_a.key, _a) for _a in APP_STATES])


def by_key(key):
    """Get an application state by key"""
    if isinstance(key, models.AppState):
        return key
    try:
        return APP_STATE_MAP[key]
    except KeyError:
        raise ValueError("Undefined app state", key)
