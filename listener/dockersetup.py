#! /usr/bin/python
"""process to create and run the dockerised daemon

the container we create contains mostly the underlying libraries
with the actual code mapped into the demon from the installation
directory of the code here

we map the video card from the host into the container
so this should not be considered a safe operation on a multi user host
but should be reasonable on a single seat device.
"""
import subprocess, os, sys, logging, requests, glob
from . import defaults

log = logging.getLogger(__name__)
HERE = os.path.dirname(os.path.abspath(__file__))


def cache_models(
    version=defaults.DEFAULT_DEEPSPEECH_VERSION, cache_dir=defaults.MODEL_CACHE
):
    """Cache the deepspeech models in user's cache directory
    
    the deep speech models are quite large files which are updated
    less frequently than the deep speech code itself
    """
    for template in [
        defaults.MODEL_FILE,
        defaults.SCORER_FILE,
    ]:
        filename = template % locals()
        local = os.path.join(cache_dir, filename)
        if not os.path.exists(local):
            url = (defaults.RELEASE_URL % locals()) + filename
            log.warning(
                'Downloading %s => %s', url, local,
            )
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)
            tmp = local + '~'
            headers = {}
            if os.path.exists(tmp):
                start = os.stat(tmp).st_size
                headers['Range'] = '%s-' % (start,)
            response = requests.get(
                url, allow_redirects=False, stream=True, headers=headers
            )
            if response.status_code in (301, 302):
                response = requests.get(
                    response.headers['Location'], stream=True, headers=headers
                )
            response.raise_for_status()
            total = 0
            if 'Content-length' in response.headers:
                total = int(response.headers['Content-length'])
                log.info("Downloading %sMB", total // 1000000)
            count = 0
            with open(tmp, 'ab+') as fh:
                for chunk in response.iter_content(1024 * 1024):
                    fh.write(chunk)
                    count += len(chunk)
                    log.debug(
                        " % 8iMB %s",
                        count // 1000000,
                        '(%0.2f%%)' % (100 * count / total) if total else '?',
                    )
            os.rename(tmp, local)
        else:
            log.debug(
                'Already have %s in %s', filename, cache_dir,
            )


def find_nvidia_cards():
    """Linux-specific code to look for nvidia devices in /dev/dri"""
    listing = subprocess.check_output(
        'lspci | grep -i vga | grep -i nvidia', shell=True
    )
    listing = listing.decode('ascii', 'ignore')
    devices = []
    for line in listing.strip().splitlines():
        address = line.split()[0]
        for link in glob.glob('/dev/dri/by-path/pci-0000:%s-*' % (address,)):
            devices.append(os.path.join(os.path.dirname(link), os.readlink(link),))
    if not devices:
        log.error("Unable to find any nvidia cards with lspci")
        raise SystemExit(2)
    log.info("Considering the following cards nVidia devices: %s", ' '.join(devices))
    return devices


def get_options():
    import argparse

    parser = argparse.ArgumentParser(description='Run DeepSpeech in a container')
    parser.add_argument(
        '-c',
        '--card',
        default=None,
        type=int,
        help='Which video card (0-indexed) to use for the GPU in the container (default all local nvidia cards)',
    )
    parser.add_argument(
        '-r',
        '--run',
        default=defaults.RUN_DIR,
        help='Directory in which to mount audio input pipe, default: %s'
        % (defaults.RUN_DIR,),
    )
    parser.add_argument(
        '--cache',
        default=defaults.CACHE_DIR,
        help='User model cache directory (default: %s)' % (defaults.CACHE_DIR,),
    )
    parser.add_argument(
        '--version',
        default=defaults.DEFAULT_DEEPSPEECH_VERSION,
        help='DeepSpeech version/release to use (default: %s)'
        % (defaults.DEFAULT_DEEPSPEECH_VERSION,),
    )
    parser.add_argument(
        '-b',
        '--build',
        default=False,
        action='store_true',
        help='If specified, force rebuilding of the docker image',
    )
    parser.add_argument(
        '-s',
        '--shell',
        default=False,
        action='store_true',
        help='If specified, run an interactive shell instead of a background daemon',
    )
    parser.add_argument(
        '--stop',
        default=False,
        action='store_true',
        help='If specified, halt the current docker process',
    )
    return parser


def main():
    options = get_options().parse_args()
    model_cache = os.path.join(options.cache, 'model')
    cache_models(version=options.version, cache_dir=model_cache)
    docker_name = defaults.DOCKER_CONTAINER
    images = (
        subprocess.check_output(['docker', 'images', defaults.DOCKER_IMAGE])
        .decode('utf-8')
        .strip()
        .splitlines()
    )
    if options.build or len(images) < 2:
        command = [
            'docker',
            'build',
            '--build-arg',
            'DEEPSPEECH_VERSION=%s' % (options.version,),
            '--build-arg',
            'UID=%s' % (os.geteuid(),),
            '-t',
            '%s:%s' % (defaults.DOCKER_IMAGE, options.version,),
            '-t',
            '%s:latest' % (defaults.DOCKER_IMAGE,),
            os.path.join(HERE, '../docker'),
        ]
        subprocess.check_call(command)
    if options.stop:
        for command in [
            ['docker', 'stop', docker_name],
            ['docker', 'rm', docker_name],
        ]:
            subprocess.call(command)  # Note: *not* checked...
    if not os.path.exists(options.run):
        os.makedirs(options.run)
    if options.card is not None:
        devices = [
            '--device',
            '/dev/dri/card%d' % (options.card,),
            '--device',
            '/dev/dri/renderD%d' % (128 + options.card,),
        ]
    else:
        devices = []
        for device in find_nvidia_cards():
            devices.extend(['--device', device])
    if options.shell:
        shell = ['/bin/bash']
        shell_opts = ['-it']
    else:
        shell = []
        shell_opts = ['-d']
    command = (
        ['docker', 'run',]
        + shell_opts
        + [
            '-v%s:/src/run' % (os.path.abspath(options.run),),
            '-v%s:/src/working' % (os.path.abspath(os.path.join(HERE, '..'))),
            '-v%s:/src/model' % (os.path.abspath(model_cache),),
            '-eDEEPSPEECH_VERSION=%s' % (options.version,),
            '--name',
            defaults.DOCKER_CONTAINER,
        ]
        + devices
        + ['%s:%s' % (defaults.DOCKER_IMAGE, options.version,),]
        + shell
    )
    log.info("%s", " ".join(command))
    os.execvp(command[0], command)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
