"""Install the DBus Service file into current session dbus"""
import os, sys, shutil, logging
from . import defaults, models

log = logging.getLogger(__name__)

SERVICE_TEMPLATE = '''[D-BUS Service]
Name=%(service_name)s
Exec=%(executable)s
'''


def register_dbus(service_name=defaults.DBUS_NAME, executable=None):
    """Install our service file into user's dbus service dir"""
    data_home = os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
    service_dir = os.path.join(data_home, 'dbus-1/services')
    if executable is None:
        executable = os.path.join(os.path.dirname(sys.executable), 'listener-dbus',)
    service_file = os.path.join(service_dir, '%s.service' % (service_name,))
    log.info("%s => %s", service_name, executable)
    content = SERVICE_TEMPLATE % locals()
    models.atomic_write(service_file, content)
    return service_file


def get_options():
    import argparse

    parser = argparse.ArgumentParser(
        description='Registers this virtualenv copy of listener-dbus for our published service name'
    )
    parser.add_argument(
        '-v',
        '--verbose',
        default=False,
        action='store_true',
        help='Enable verbose logging (for developmen/debugging)',
    )
    return parser


def main():
    options = get_options().parse_args()
    defaults.setup_logging(options)
    register_dbus()
