"""Python 2/3 compatibility layer"""
import sys

STR_IS_BYTES = True

if sys.version_info[:2] < (2, 6):
    # no bytes, traditional setup...
    bytes = str
else:
    bytes = bytes
try:
    long = long
except NameError as err:
    long = int
if sys.version_info[:2] < (3, 0):
    # traditional setup, with bytes defined...
    unicode = unicode
    _NULL_8_BYTE = '\000'

    def as_bytes(target, encoding='utf-8'):
        """Ensure target is bytes, using encoding to encode if is unicode"""
        if isinstance(target, unicode):
            return target.encode(encoding)
        return bytes(target)

    def as_unicode(target, encoding='utf-8'):
        """Ensure target is unicode, using encoding to decode if is bytes"""
        if isinstance(target, bytes):
            try:
                return target.decode(encoding)
            except UnicodeError:
                try:
                    return target.decode('utf-8')
                except UnicodeError:
                    return target.decode('latin-1')
        return unicode(target)

    integer_types = int, long
else:
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
