"""Python 2/3 compatibility layer"""
import sys

STR_IS_BYTES = True

long = int
unicode = str
# new setup, str is now unicode...
STR_IS_BYTES = False
_NULL_8_BYTE = bytes('\000', 'latin1')


def as_bytes(target, encoding='utf-8'):
    """Ensure target is bytes, using encoding to encode if is unicode"""
    if isinstance(target, unicode):
        return target.encode(encoding)
    elif isinstance(target, bytes):
        # Note: this can create an 8-bit string that is *not* in encoding,
        # but that is potentially exactly what we wanted, as these can
        # be arbitrary byte-streams being passed to C functions
        return target
    return str(target).encode(encoding)


def as_unicode(target, encoding='utf-8'):
    """Ensure target is unicode, using encoding to decode if is bytes"""
    if isinstance(target, bytes):
        return target.decode(encoding)
    return unicode(target)


unicode = str
integer_types = (int,)

STR_IS_UNICODE = not STR_IS_BYTES
if hasattr(sys, 'maxsize'):
    maxsize = sys.maxsize
else:
    maxsize = sys.maxint
