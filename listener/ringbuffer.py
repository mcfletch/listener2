"""Numpy-backed ringbuffer with direct read from named pipe or socket"""
import logging
import numpy as np
from . import defaults

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


class RingBuffer(object):
    """Crude numpy-backed ringbuffer"""

    def __init__(self, duration=30, rate=defaults.SAMPLE_RATE):
        self.duration = duration
        self.rate = rate
        self.size = duration * rate
        self.buffer = np.zeros((self.size,), dtype=np.int16)
        self.write_head = 0
        self.start = 0

    def read_in(self, file_handle, blocksize=1024):
        """Read in content from the buffer"""
        target = self.buffer[self.write_head : self.write_head + blocksize]
        if hasattr(file_handle, 'readinto'):
            # On the blocking fifo this consistently reads
            # the whole blocksize chunk of data...
            written = file_handle.readinto(target)
            if written != blocksize * 2:
                log.debug(
                    "Didn't read the whole buffer (likely disconnect): %s/%s",
                    written,
                    blocksize // 2,
                )
                target = target[: (written // 2)]
        else:
            # This is junk, unix and localhost buffering in ffmpeg
            # means we take 6+ reads to get a buffer and we wind up
            # losing a *lot* of audio due to delays
            tview = target.view(np.uint8)
            written = 0
            reads = 0
            while written < blocksize:
                written += file_handle.recv_into(tview[written:], blocksize - written)
                reads += 1
            if reads > 1:
                log.debug("Took %s reads to get %s bytes", reads, written)
        self.write_head = (self.write_head + written) % self.size
        return target

    def itercurrent(self):
        """Iterate over all samples in the current record
        
        After we truncate from the beginning we have to
        reset the stream with the content written already
        """
        if self.write_head < self.start:
            yield self.buffer[self.start :]
            yield self.buffer[: self.write_head]
        else:
            yield self.buffer[self.start : self.write_head]

    def __len__(self):
        """Calculate how much data is between end-of-last-read and current-write-head"""
        if self.write_head < self.start:
            return self.size - self.start + self.write_head
        else:
            return self.write_head - self.start
