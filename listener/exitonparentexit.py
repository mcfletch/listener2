import ctypes, signal

libc = ctypes.CDLL("libc.so.6")


def exit_on_parent_exit():
    return libc.prctl(1, signal.SIGTERM)
