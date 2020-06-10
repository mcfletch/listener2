#! /usr/bin/env python3
"""Non-working attempt to get a clean/signal-able ffmpeg to named pipe pipeline"""
import os, subprocess, logging, time, re

log = logging.getLogger(__name__)

DEFAULT_TARGET = '/run/user/%s/recogpipe/audio' % (os.geteuid(),)

DEVICE_DEFINTION = re.compile(
    r'^card (?P<card>\d+)[:].*[[](?P<name>[^]]+)[]], device (?P<device>\d+)[:]'
)


def get_alsa_devices():
    """Retrieve the list of alsa recording devices on this machine"""
    content = subprocess.check_output(['arecord', '-l']).decode('ascii', 'ignore')
    result = []
    for line in content.splitlines():
        match = DEVICE_DEFINTION.match(line)
        if match:
            result.append(match.groupdict())
    result.sort(key=lambda x: (x['card'], x['device']))
    return result


def device_as_hw_name(device):
    return 'hw:%(card)s,%(device)s' % device


def get_options():
    import argparse

    parser = argparse.ArgumentParser(
        description='Use ALSA arecord to pipe audio to recogpipe',
    )
    # device = parser.add_argument(
    #     '-d','--device',
    #     default=None,
    #     help='Device to use for input, leave off to list devices',
    # )
    parser.add_argument(
        '-t',
        '--target',
        default=DEFAULT_TARGET,
        help='Named pipe to which to record (default: %s)' % (DEFAULT_TARGET,),
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
    logging.basicConfig(
        level=logging.DEBUG if options.verbose else logging.INFO,
        format='%(levelname) 7s %(name)s:%(lineno)s %(message)s',
    )
    # if not options.device:
    #     log.info("ALSA Devices:")
    #     for record in get_alsa_devices():
    #         log.info("  %s => %s", device_as_hw_name(record), record['name'])
    #     return 0
    target = options.target
    # audio_hw = options.device
    # if audio_hw.isdigit():
    #     record = get_alsa_devices()[int(options.device)]
    #     audio_hw = device_as_hw_name(record)
    #     log.info("Choosing input %s => %s", audio_hw, record['name'])
    # hw = audio_hw
    directory = os.path.dirname(target)
    if not os.path.exists(target):
        log.info("Creating fifo in %s", target)
        os.mkfifo(target)
    # Sigh, the use of a device winds up messing up mono input
    command = [
        'arecord',
        # '-D',hw,
        '-t',
        'raw',
        '--rate',
        '16000',
        '-f',
        's16_le',
        # '-c','2',
        target,
    ]
    log.info("Command: %s", " ".join(command))
    os.execvp(command[0], command)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
