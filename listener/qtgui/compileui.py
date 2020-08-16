"""Simple script to compile UI files"""
import glob, subprocess, os
from .. import defaults

RESOURCES = os.path.join(defaults.LISTENER_SOURCE, 'static')


def main():
    for filename in glob.glob(os.path.join(RESOURCES, '*.ui')):
        base = os.path.basename(filename)[:-3]
        target = os.path.join(RESOURCES, base + '.py')
        if (
            os.path.exists(target)
            and os.stat(target).st_mtime > os.stat(filename).st_mtime
        ):
            continue
        subprocess.check_output(
            ['pyside2-uic', '-o', target, filename,]
        )

