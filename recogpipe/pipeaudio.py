#! /usr/bin/env python3
"""Non-working attempt to get a clean/signal-able ffmpeg to named pipe pipeline"""
import os, subprocess, logging, time, re
log = logging.getLogger(__name__)

DEVICE_DEFINTION = re.compile(r'^card (?P<card>\d+)[:].*[[](?P<name>[^]]+)[]], device (?P<device>\d+)[:]')

def get_alsa_devices():
    """Retrieve the list of alsa recording devices on this machine"""
    content = subprocess.check_output(['arecord','-l']).decode('ascii','ignore')
    result = []
    for line in content.splitlines():
        match = DEVICE_DEFINTION.match(line)
        if match:
            result.append(match.groupdict())
    result.sort(key =lambda x: (x['card'],x['device']))
    return result

def get_options():
    import argparse
    parser = argparse.ArgumentParser(
        description='Use ALSA arecord to pipe audio to recogpipe',
    )
    device = parser.add_argument(
        '-d','--device',
        default=None,

    )

    return parser

def main():
    log.info("ALSA Devices:")
    for record in get_alsa_devices():
        log.info("hw:%(card)s,%(device)s => %(name)s"%record)
    audio_hw = 'hw:1,0'
    hw = audio_hw
    uid = os.geteuid()
    target = '/run/user/%s/recogpipe/audio'%(uid,)
    directory = os.path.dirname(target)
    if not os.path.exists(target):
        log.info("Creating fifo in %s", target)
        os.mkfifo(target)

    command = [
        'arecord','-D',hw,'-t','raw','--rate','16000','-f','s16_le','-c','1',target 
    ]
    log.info("Command: %s", " ".join(command))
    os.execvp(command[0],command)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main() 
