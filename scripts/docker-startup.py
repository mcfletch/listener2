#! /usr/bin/env python3
import logging, os, subprocess, sys, pwd


def main():
    os.chdir('/src/working')
    subprocess.check_call(
        ['python3', 'setup.py', 'install',]
    )
    user = pwd.getpwnam('deepspeech')
    os.setuid(user.pw_gid)
    os.setuid(user.pw_uid)
    command = ['recogpipe-daemon', '-v'] + sys.argv[1:]
    os.execvp(command[0], command)


if __name__ == '__main__':
    main()
