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
log = logging.getLogger(__name__)
HERE = os.path.dirname(os.path.abspath(__file__))

USER_CACHE_DIR = os.environ.get('XDG_CACHE_HOME',os.path.expanduser('~/.cache'))
CACHE_DIR = os.path.join(USER_CACHE_DIR,'recogpipe')
MODEL_CACHE = os.path.join(CACHE_DIR,'model')
DEFAULT_VERSION = '0.7.3'
RELEASE_URL = 'https://github.com/mozilla/DeepSpeech/releases/download/v%(version)s/'
MODEL_FILE = 'deepspeech-%(version)s-models.pbmm'
SCORER_FILE= 'deepspeech-%(version)s-models.scorer'

USER_RUN_DIR = os.environ.get('XDG_RUNTIME_DIR','/run/user/%s'%(os.geteuid()))
RUN_DIR = os.path.join(USER_RUN_DIR,'recogpipe')
DEFAULT_INPUT = os.path.join(RUN_DIR,'audio')

def get_username():
    """get the current users user name"""
    import pwd
    return pwd.getpwuid(os.geteuid()).pw_name

def cache_models(version=DEFAULT_VERSION, cache_dir=MODEL_CACHE):
    """Cache the deepspeech models in user's cache directory
    
    the deep speech models are quite large files which are updated
    less frequently than the deep speech code itself
    """
    for template in [
        MODEL_FILE,
        SCORER_FILE,
    ]:
        filename = template%locals()
        local = os.path.join(cache_dir,filename)
        if not os.path.exists(local):
            url = (RELEASE_URL%locals()) + filename
            log.warning(
                'Downloading %s => %s',
                url, local,
            )
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)
            tmp = local + '~'
            headers = {}
            if os.path.exists(tmp):
                start = os.stat(tmp).st_size
                headers['Range'] = '%s-'%(start,)
            response = requests.get(url,allow_redirects=False,stream=True,headers=headers)
            if response.status_code in (301,302):
                response = requests.get(response.headers['Location'],stream=True,headers=headers)
            response.raise_for_status()
            total = 0
            if 'Content-length' in response.headers:
                total = int(response.headers['Content-length'])
                log.info("Downloading %sMB", total//1000000)
            count = 0
            with open(tmp,'ab+') as fh:
                for chunk in response.iter_content(1024*1024):
                    fh.write(chunk)
                    count += len(chunk)
                    log.debug(" % 8iMB %s",count//1000000,'(%0.2f%%)'%(100*count/total) if total else '?')
            os.rename(tmp,local)
        else:
            log.debug(
                'Already have %s in %s', filename, cache_dir,
            )

def find_nvidia_cards():
    """Linux-specific code to look for nvidia devices in /dev/dri"""
    listing = subprocess.check_output('lspci | grep -i vga | grep -i nvidia',shell=True)
    listing = listing.decode('ascii','ignore')
    devices = []
    for line in listing.strip().splitlines():
        address = line.split()[0]
        for link in glob.glob('/dev/dri/by-path/pci-0000:%s-*'%(address,)):
            devices.append(
                os.path.join(
                    os.path.dirname(link),
                    os.readlink(link),
                )
            )
    if not devices:
        log.error("Unable to find any nvidia cards with lspci")
        raise SystemExit(2)
    return devices

def get_options():
    import argparse
    parser = argparse.ArgumentParser(description='Run DeepSpeech in a container')
    parser.add_argument(
        '-c','--card',
        default = None,
        type = int,
        help='Which video card (0-indexed) to use for the GPU in the container (default all local nvidia cards)',
    )
    parser.add_argument(
        '-r','--run',
        default = RUN_DIR,
        help='Directory in which to mount audio input pipe, default: %s'%(RUN_DIR,)
    )
    parser.add_argument(
        '--cache',
        default=CACHE_DIR,
        help='User model cache directory (default: %s)'%(CACHE_DIR,)
    )
    parser.add_argument(
        '--version',
        default=DEFAULT_VERSION,
        help='DeepSpeech version/release to use (default: %s)'%(DEFAULT_VERSION,),
    )
    parser.add_argument(
        '-b','--build',
        default=False,
        action='store_true',
        help='If specified, force rebuilding of the docker image',
    )
    parser.add_argument(
        '-s','--shell',
        default=False,
        action='store_true',
        help='If specified, run an interactive shell instead of a background daemon',
    )
    parser.add_argument(
        '--stop',
        default = False,
        action = 'store_true',
        help = 'If specified, halt the current docker process',
    )
    return parser

def main():
    options = get_options().parse_args()
    model_cache = os.path.join(options.cache,'model')
    cache_models(version=options.version, cache_dir=model_cache)
    docker_name = 'recogpipe_%s'%(get_username())
    images = subprocess.check_output([
        'docker','images','deepspeech-client'
    ]).decode('utf-8').strip().splitlines()
    if options.build or len(images) < 2:
        command = [
            'docker',
                'build',
                '--build-arg','DEEPSPEECH_VERSION=%s'%(options.version,),
                '--build-arg','UID=%s'%(os.geteuid(),),
                '-t', 'recogpipe-server:%s'%(options.version,),
                '-t', 'recogpipe-server:latest',
            os.path.join(HERE,'../docker'),
        ]
        subprocess.check_call(command)
    if options.stop:
        for command in [
            ['docker','stop',docker_name],
            ['docker','rm',docker_name],
        ]:
            subprocess.call(command) # Note: *not* checked...
        return 0
    if not os.path.exists(options.run):
        os.makedirs(options.run)
    if options.card is not None:
        devices = [
            '--device','/dev/dri/card%d'%(options.card,),
            '--device','/dev/dri/renderD%d'%(128+options.card,),
        ]
    else:
        devices = []
        for device in find_nvidia_cards():
            devices.extend([
                '--device',
                device
            ])
    if options.shell:
        shell = ['/bin/bash']
        shell_opts = ['-it']
    else:
        shell = []
        shell_opts = ['-d']
    command = [
        'docker','run',
    ] + shell_opts + [
        '-v%s:/src/run'%(os.path.abspath(options.run),),
        '-v%s:/src/working'%(os.path.abspath(os.path.join(HERE,'..'))),
        '-v%s:/src/model'%(os.path.abspath(model_cache),),
        '-eDEEPSPEECH_VERSION=%s'%(options.version,),
        '--name', 'recogpipe_%s'%(get_username()),
    ] + devices + [
        '--user','deepspeech',
        'recogpipe-server:%s'%(options.version,),
    ] + shell
    log.info("%s", " ".join(command))
    os.execvp(command[0],command)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
