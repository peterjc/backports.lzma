# Copyright 2012-13 by Peter Cock.
# All rights reserved.
"""Python module for random access to blocked XZ files (LMZA compression).

Python 3.3 includes the moudle lmza which allows read and write access
to XZ files, however random access is emulated and is slow (much like
with Python's gzip module).

Biopython's bgzf module supports efficient random access to BGZF files,
Blocked GNU Zip Format, a variant of GZIP using blocks for random access.
This was implemented as a Python module calling the library zlib (in C)
for efficient compression and decompression. Here we take a similar
approach.

Note that for multi-stream XZ files, the different streams could be using
different checksums (set in the stream header/footer). Thus we should check
they are the same, or regard any differences between streams as an error
(current approach), or simply ignore the checksum (in breach of the spec).

This work is based heavily on reading the XZ file format specification,
http://tukaani.org/xz/format.html
"""

import sys
import os
import struct
try:
    #Python 2
    import __builtin__ #to access the usual open function
except:
    #Python 3
    import builtins as __builtin__

try:
    from backports.lzma import CHECK_NONE, CHECK_CRC32, CHECK_CRC64, CHECK_SHA256
    from backports.lzma import FORMAT_RAW, FORMAT_XZ, FILTER_LZMA1, FILTER_LZMA2
    from backports.lzma import FILTER_DELTA, FILTER_X86, FILTER_POWERPC, FILTER_IA64
    from backports.lzma import FILTER_ARM, FILTER_ARMTHUMB, FILTER_SPARC
    from backports.lzma import decompress as _decompress
except ImportError:
    from lzma import CHECK_NONE, CHECK_CRC32, CHECK_CRC64, CHECK_SHA256
    from lzma import FORMAT_RAW, FORMAT_XZ, FILTER_LZMA1, FILTER_LZMA2
    from lzma import FILTER_DELTA, FILTER_X86, FILTER_POWERPC, FILTER_IA64
    from lzma import FILTER_ARM, FILTER_ARMTHUMB, FILTER_SPARC
    from lzma import decompress as _decompress

_filters = [FILTER_LZMA1, FILTER_LZMA2, FILTER_DELTA, FILTER_X86,
            FILTER_POWERPC, FILTER_IA64, FILTER_ARM, FILTER_ARMTHUMB,
            FILTER_SPARC]

import zlib #for crc32, see below
#Same sign problem with: from binascii import crc32
def crc32(bytes):
    value = zlib.crc32(bytes)
    if value < 0:
        #Nasty cross-platform hack due to signed vs unsigned checksum:
        return 4294967296 + value
    return value

from io import BytesIO

_stream_header_magic = b"\xfd7zXZ\x00"
_stream_footer_magic = b"YZ"
_empty_bytes_string = b""
_null = b"\0"

class CheckSumError(ValueError):
    pass

#Simpler and faster to have two versions of this (Python 2 and 3)
if sys.version_info[0] == 2:
    def _encode_variable_int(value):
        """Format an integer using XZ variable length encoding.

        Based on the C function decode given in the XZ specification.
        Essentially this uses base 128 (i.e. 2**7), with the top bit
        set to indicate another byte/digit is required, giving the
        least significant digit/byte first.
        """
        if value > 2**63:
            raise OverflowError(value)

        answer = _empty_bytes_string
        while (value >= 0x80):
            answer += chr( (value % 128) | 0x80)
            value >>= 7
        answer += chr(value % 128)
        return answer
else:
    #Python 3 or later
    def _encode_variable_int(value):
        """Format an integer using XZ variable length encoding.

        Based on the C function decode given in the XZ specification.
        Essentially this uses base 128 (i.e. 2**7), with the top bit
        set to indicate another byte/digit is required, giving the
        least significant digit/byte first.
        """
        if value > 2**63:
            raise OverflowError(value)

        answer = []
        while (value >= 0x80):
            answer.append( (value % 128) | 0x80)
            value >>= 7
        answer.append(value % 128)
        return bytes(answer)

assert _encode_variable_int(7) == b"\x07", \
    "_encode_variable_int(7) --> %r" % _encode_variable_int(7)

def _decompress_block(block_with_check, uncomp_size):
    check = b"\x00\x04"
    #Strip the checksum (assume 3 bytes)
    #block = block_with_check[:29]
    block = block_with_check[:-3].rstrip(_null)
    print("Striped block from %i to just %i" % (len(block_with_check), len(block)))
    print("Generating dummy index for one block %r length %i, uncomp len %i" % (block, len(block), uncomp_size))
    #Variable encoding of one (1 block) is 0x1,
    dummy_index = _null + b"\x01" \
        + _encode_variable_int(len(block)) \
        + _encode_variable_int(uncomp_size)
    pad = len(dummy_index) % 4
    if pad:
        dummy_index += _null * (4 - pad)

    dummy_index += struct.pack("<I", crc32(dummy_index))
    dummy_footer = struct.pack("<I", (len(dummy_index)//4) - 1) + check
    dummy_footer = struct.pack("<I", crc32(dummy_footer)) \
        + dummy_footer + _stream_footer_magic

    dummy_head = _stream_header_magic + check + struct.pack("<I", crc32(check))

    #pad = len(block) % 4
    #if pad:
    #    block += _null * (4 - pad)
    assert len(block_with_check) % 4 == 0, len(block_with_check) % 4

    print("Adding index %r and %r footer" % (dummy_index, dummy_footer))
    block = dummy_head + block_with_check + dummy_index + dummy_footer
    print("Attempting to decompressed %r (dummy stream)" % block)
    block = _decompress(block)
    assert len(block) == uncomp_size
    print("Worked, got %r back" % block)
    return block
#assert b"Hello" == _decompress_block(b'\x02\x00!\x01\x16\x00\x00\x00t/\xe5\xa3\x01\x00\x04Hello\x00\x00\x00\x00\xc8\xac{\xc8;\\\xcfQ', 5)

def _parse_variable_int(buffer, offset=0):
    """Read variable length encoded integer from buffer.

    Return 2-tuple of new buffer offset (i.e. input offset argument
    incremented by the number of bytes used to encode the value)
    and the value.

    Based on the C function decode given in the XZ specification.
    Essentially this uses base 128 (i.e. 2**7), with the top bit
    set to indicate another byte/digit is required, giving the
    least significant digit/byte first.
    """
    length, value = _get_variable_int(BytesIO(buffer[offset:]))
    return offset + length, value

def _get_variable_int(handle):
    """Read a variable length encoded integer from XZ file handle.

    Returns a tuple, number of bytes used, and the value.
    
    Based on the C function decode given in the XZ specification.
    Essentially this uses base 128 (i.e. 2**7), with the top bit
    set to indicate another byte/digit is required, giving the
    least significant digit/byte first.

    TODO - Make this work from a bytes string & offset
    (can return the new offset and the value).
    """
    #TODO - Is this endian safe?
    i = 0
    #b = handle.read(1)[0] <-- Works on Python 3
    b = ord(handle.read(1)) #As an integer, ord(...) for Python 2
    value = b & 0x7F #Mask out the high bit (if set)
    buf = [b]
    #print(i, b, value)
    while b & 0x80: #If high bit 0x80 = 128 is set
        i += 1
        b = ord(handle.read(1))
        buf.append(b)
        if (i >= 9) or (b == _null):
            raise OverFlowError
        #Add new value is (b & 0x7F) multiplied by 128**i
        #which we can calculate using an i*7 shift
        #value |= (b & 0x7F) << (i * 7)
        value += (b & 0x7F)*(128**i)
        #print(i, b, value)
    return i+1, value

#Quick self test:
assert (1, 7) == _get_variable_int(BytesIO(b'\x07'))
assert (3, 1024**2) == _get_variable_int(BytesIO(b'\x80\x80@'))

assert (1, 7) == _parse_variable_int(b'\x07')
assert (3, 1024**2) == _parse_variable_int(b'\x80\x80@')
assert _encode_variable_int(1024**2) == b"\x80\x80@"



def _checksum_from_stream_flag(buffer):
    assert len(buffer)==2
    assert buffer[0:1] == _null, buffer
    check_sum =  ord(buffer[1:2])
    assert check_sum & 0xF0 == 0
    #As you might guess, these CHECK_* constants match the XZ values
    if check_sum == 0x00:
        return CHECK_NONE
    elif check_sum == 0x01:
        return CHECK_CRC32
    elif check_sum == 0x04:
        return CHECK_CRC64
    elif check_sum == 0x0A:
        return CHECK_SHA264
    else:
        raise ValueError("Reserved check sum value in stream flag %r" % buffer)

def _load_stream_header(handle):
    header = handle.read(12)
    assert header[0:6] == _stream_header_magic, header[0:6]
    stream_flags = header[6:8]
    crc, = struct.unpack("<I", header[8:12])
    if  crc32(header[6:8]) != crc:
        raise CheckSumError("Stream header flag's checksum failed: %r" % header)
    return stream_flags

#_footer_fmt =
def _load_stream_footer(handle):
    footer = handle.read(12)
    assert footer[10:12] == _stream_footer_magic, footer[10:12]
    crc, stored_backward_size= struct.unpack("<II", footer[0:8])
    stream_flags = footer[8:10]
    #Checksum for backward size and stream flags:
    if crc32(footer[4:10]) != crc:
        raise CheckSumError("Stream footer's backward-size/flag checksum failed: %r\ncrc32(%r) = %r vs %r" \
                                % (footer, footer[4:10], crc32(footer[4:10]), crc))
    real_backward_size = (stored_backward_size + 1) * 4;
    #TODO - Check for null padding?
    return real_backward_size, stream_flags


def _dict_size(value):
    """Decode LZMA2 filter size (4KiB to 4GiB)."""
    bits = value & 0x3F
    if bits > 40:
        raise OverflowError("LZMA2 filter dictionarry too big")
    elif bits == 40:
        return 0xffffffff # UINT32_MAX
    else:
        size = 2 | (bits & 1)
        size <<= bits // 2 + 11;
        return size
assert _dict_size(0) == 4096 # 4 KiB
assert _dict_size(1) == 6144
assert _dict_size(29) == 100663296
assert _dict_size(39) == 3221225472
assert _dict_size(40) == 0xffffffff # 4 GiB - 1 byte

def _load_stream_block_header(handle, expected_comp_size, expected_uncomp_size):
    """Returns header size and list of filters."""
    #print("Loading block header, expect comp %i --> %i" % (expected_uncomp_size, expected_comp_size))
    buf = handle.read(2)
    encoded_header_size, block_flags = struct.unpack("<BB", buf)
    assert 1 < encoded_header_size <= 0xFF, encoded_header_size
    real_header_size = (encoded_header_size + 1) * 4
    assert 6 <= real_header_size, real_header_size
    buf += handle.read(real_header_size - 2)
    offset = 2

    crc, = struct.unpack("<I", buf[-4:])
    if crc32(buf[:-4]) != crc:
        raise CheckSumError("Stream block header's checksum failed: %r" % buf)

    filter_count = (block_flags & 0x03) + 1 #allowed 1 to 4 filters
    if block_flags & 0x3C:
        # Note 0x3C = 0x4 + 0x8 + 0x10 + 0x20 = 4 + 8 + 16 + 32 = 60
        raise ValueError("Block Flag bits 0x3C reserved for future use "
                         "and should be zero (got 0x%x & 0x3C = 0x%x)."
                         % (block_flags, block_flags & 0x3C))
    if block_flags & 0x40:
        offset,  compressed_size = _parse_variable_int(buf, offset)
        assert compressed_size == expected_comp_size, \
            "Compressed size in block header %i, expected %i" \
            % (compressed_size, expected_comp_size)
    if block_flags & 0x80:
        offset, uncompressed_size = _get_variable_int(buf, offset)
        assert uncompressed_size == expected_uncomp_size, \
            "Uncompressed size in block header %i, expected %i" \
            % (uncompressed_size, expected_uncomp_size)
    filters = []
    for i in range(filter_count):
        offset, filter_id = _parse_variable_int(buf, offset)
        offset, size_of_props = _parse_variable_int(buf, offset)
        filter_props = buf[offset:offset+size_of_props]
        offset += size_of_props
        if filter_id == 0x21:
            assert size_of_props == 1
            size = ord(filter_props)
            assert not size & 0xC0, "Reserved bits in LZMA2 filter size set"
            filters.append({"id":FILTER_LZMA2, "dict_size":_dict_size(size)})
        elif filter_id in _filters:
            raise NotImplementedError("TODO, filter ID %r" % filter_id)
        else:
            raise ValueError("Unknown filter ID %r" % filter_id)
        #print("Filter %i of %i, props %r (len %i)" % (i+1, filter_count, filter_props, size_of_props))
    pad = real_header_size - 4 - offset #Last 4 are the CRC
    assert len(buf) == real_header_size
    assert buf[offset:-4] == _null * pad, \
        "Expected %i null bytes of padding, not %r (%i bytes)" \
        % (real_header_size - offset, buf[offset:-4], len(buf[offset:-4]))
    crc, = struct.unpack("<I", buf[-4:])
    if crc32(buf[:-4]) != crc:
        raise CheckSumError("Stream block header's checksum failed: %r" % buf)
    return real_header_size, filters
_hello = b'\x02\x00!\x01\x16\x00\x00\x00t/\xe5\xa3\x01\x00\x04Hello\x00\\x00\x00\x00\xc8\xac{\xc8;\\\xcfQ'
assert (12, [{'dict_size': 8388608, 'id': 33}]) == _load_stream_block_header(BytesIO(_hello), None, None)
if _decompress:
    assert b'Hello' == _decompress(_hello[12:21], format=FORMAT_RAW, filters=[{'dict_size': 8388608, 'id': 33}])

def _load_stream_index(handle, expected_size):
    assert expected_size % 4 == 0, expected_size
    buf = handle.read(expected_size)
    assert buf[0:1] == _null, "Stream index started with %r not null" % buf[0:1]
    crc, = struct.unpack("<I", buf[-4:])
    if crc32(buf[:-4]) != crc:
        import warnings
        warnings.warn("Stream index's checksum failed (or size was wrong), %r vs %s" % (crc32(buf[:-4]), crc))
        #raise CheckSumError("Stream index's checksum failed (or size was wrong)")

    offset = 1
    offset, record_count = _parse_variable_int(buf, offset)
    #print("Index contains %i records" % record_count)
    for record in range(record_count):
        offset, unpadded_size = _parse_variable_int(buf, offset)
        offset, uncompressed_size = _parse_variable_int(buf, offset)
        #print("Record %i, unpadded size %i, uncompressed size %i" % (record, unpadded_size, uncompressed_size))
        yield unpadded_size, uncompressed_size
    if offset % 4 != 0:
        #Check null padding...
        pad = 4 - (offset % 4)
        assert buf[offset:offset + pad] == _null * pad, buf[offset:offset + pad]
        offset += pad
    assert offset + 4 == expected_size, "Stream index size %i, expected %i" % (offset+4, expected_size)
    if crc32(buf[:-4]) != crc:
        import warnings
        warnings.warn("Stream index's checksum failed")
        #raise CheckSumError("Stream index's checksum failed")

def _load_index(h, size=None):
    """Goes to the end of the XZ file and works its way backwards.

    At the end of each XZ stream, just before the stream footer,
    is a stream index which gives the sizes of the data blocks
    in that stream (which we can use for finding block starts).
    This stream index also tells us the start position of the
    stream, and this the end of any preceeding stream.

    Once we have the stream index information from all the streams,
    we can infer the compressed data position corresponding to
    each block of data.

    The return value of this function is a first of all list of
    tuples, one for each block, and a dummy block for the end of
    the file:

     - start offset on disk of the compressed block
     - start offset of decompressed data in this block

    The dummy block is included so the compressed and uncompressed
    size of any block an be calculated.

    Additionally it returns the number of streams (integer, min 1),
    and the size of the largest uncompressed block (for convience).

    To perform a random access seek to a given position in the
    decompressed data, use the second list to find which block
    it is contained in (and how far into that block's decompressed
    data, i.e. the within-block-offset), and then use the matching
    entry in the first list to get the raw offset on disk for that
    block (i.e. the block-start-offset), and decompress that (all
    into RAM if you like, or incrementally).
    """
    h.seek(0)
    stream_flag = _load_stream_header(h)
    checksum_function = _checksum_from_stream_flag(stream_flag)

    if size is None:
        size = os.fstat(h.fileno()).st_size
    #print("File size is %i" % size)

    stream_count = 0
    block_starts_and_uncomp_sizes = []

    total_uncomp_size = 0
    stream_end = size
    while stream_end > 0:
        stream_count += 1
        #print("---")
        #print("Scanning stream ending at %i" % stream_end)
        h.seek(stream_end - 12)
        back_size, footer_stream_flag = _load_stream_footer(h)
        h.seek(stream_end - 12 - back_size)
        block_sizes = list(_load_stream_index(h, back_size))
        #print("Stream ending at %i has %i blocks, ending at %i" % (stream_end, len(block_sizes), stream_end - 12 - back_size))
        stream_comp_size = 0
        stream_uncomp_size = 0
        for unpadded_size, uncompressed_size in block_sizes[::-1]:
            #Round up unpadded size to multiple of four
            if unpadded_size % 4:
                padded_size = unpadded_size + 4 - (unpadded_size % 4)
            else:
                padded_size = unpadded_size
            #print("Block size %i (padded %i) --> %i" % (unpadded_size, padded_size, uncompressed_size))
            stream_comp_size += padded_size
            stream_uncomp_size += uncompressed_size
            #Sanity test, does the block header agree?
            block_start = stream_end - 12 - back_size - stream_comp_size
            block_end = block_start + padded_size
            #print("Block location %i to %i, size %i (padded %i) --> %i" \
            #          % (block_start, block_end, unpadded_size, padded_size, uncompressed_size))
            h.seek(block_start)
            _load_stream_block_header(h, unpadded_size, uncompressed_size)
            block_starts_and_uncomp_sizes.append((block_start, unpadded_size, uncompressed_size))
        assert stream_comp_size % 4 == 0
        #print("Stream %i --> %i (%0.1f%%)" % (stream_uncomp_size, stream_comp_size, stream_comp_size*100.0/stream_uncomp_size))
        stream_start = stream_end - 12 - back_size - stream_comp_size - 12
        #print("Appears stream location is %i to %i ..." % (stream_start, stream_end))
        assert stream_start >= 0, stream_start
        h.seek(stream_start)
        header_stream_flag = _load_stream_header(h)
        assert header_stream_flag == footer_stream_flag
        if stream_flag != header_stream_flag:
            raise ValueError("Multiple streams with different flags found, %r vs %r" \
                             % (stream_flag, header_stream_flag))
        #print("Confirmed stream location is %i to %i, flag %r" % (stream_start, stream_end, header_stream_flag))
        #Check preceeding stream (if any)
        stream_end = stream_start
        total_uncomp_size += stream_uncomp_size
    #print("--")
    assert stream_end == 0, stream_end

    #Now that we've got to the start of the file, work out uncomp block starts
    total_uncompressed = 0
    max_uncomp_block = 0
    blocks = []
    for block_start, unpadded_size, uncompressed_size in block_starts_and_uncomp_sizes[::-1]:
        max_uncomp_block = max(max_uncomp_block, uncompressed_size)
        blocks.append((block_start, total_uncompressed, unpadded_size))
        total_uncompressed += uncompressed_size
        #TODO - Rather than using a triple-tuple, can we ensure that the
        #jump in block_start gives the (padded) block size by including
        #dummy entries where we have a stream end/start?
    blocks.append((size, total_uncompressed, 0))
    print("End", size, total_uncompressed)
    assert total_uncompressed == total_uncomp_size
    return blocks, stream_count, max_uncomp_block
#import lzma
#_hello = lzma.compress(b"Hello")
_hello = b'\xfd7zXZ\x00\x00\x04\xe6\xd6\xb4F\x02\x00!\x01\x16\x00\x00\x00t/\xe5\xa3\x01\x00\x04Hello\x00\x00\x00\x00\xc8\xac{\xc8;\\\xcfQ\x00\x01\x1d\x05\xb8-\x80\xaf\x1f\xb6\xf3}\x01\x00\x00\x00\x00\x04YZ'
assert ([(12, 0, 29), (64, 5, 0)], 1, 5) == _load_index(BytesIO(_hello), len(_hello)), _load_index(BytesIO(_hello), len(_hello))

class XzReader(object):
    """XZ reader, acts like a read only handle but caches XZ blocks for random access.
    """
    def __init__(self, filename=None, mode="r", fileobj=None,
                 max_cache=100, max_block_size=100000):
        if max_cache < 1:
            raise ValueError("Use max_cache with a minimum of 1 (number of blocks to cache)")
        if max_block_size < 0:
            raise ValueError("Need positive max_block_size (or zero for unlimited)")
        #Must open the XZ file in binary mode, but we may want to
        #treat the contents as either text or binary (unicode or
        #bytes under Python 3)
        if fileobj:
            assert filename is None
            handle = fileobj
            assert "b" in handle.mode.lower()
        else:
            if "w" in mode.lower() \
            or "a" in mode.lower():
                raise ValueError("Must use read mode (default), not write or append mode")
            handle = __builtin__.open(filename, "rb")
        self._text = "b" not in mode.lower()
        if self._text:
            self._newline = "\n"
        else:
            self._newline = _bytes_newline
        self._handle = handle
        self.max_cache = max_cache
        self.max_block_size = max_block_size
        self._buffers = {}
        handle.seek(0)
        self._magic = handle.read(12)
        self._magic_foot = _null*8 + self._magic[6:8] + b'YZ'
        handle.seek(0)
        self._index, streams, max_block = _load_index(handle)
        if max_block > max_block_size:
            if not fileobj:
                #We didn't open it, so we won't close it:
                handle.close()
            #TODO - Fall back on incremenal decompression & emulated seeking?
            raise ValueError("This XZ file contains a block which decompresses to %i bytes "
                             "(over the limit specified of %i)" \
                                 % (max_block, max_block_size))
        self._load_block(0)
        

    def tell(self):
        """Returns offset in the uncompressed contents of the XZ file.

        This is NOT going to match the actual offset within the compressed file.
        """
        return self._index[self._block][1] + self._within_block_offset

    def seek(self, offset, whence=0):
        """Seek to a given offset in the uncompressed XZ file."""
        length = self._index[-1][1]
        if whence == 0: #SEEK_SET
            pass
        elif whence == 1: #SEEK_CUR
            offset += self._pos
        elif whence == 2: #SEEK_END
            #Offset is usually negative in this case
            offset += length
        else:
            raise ValueError("Unsupport whence value %r" % whence)
        if offset < 0 or length < offset:
            raise ValueError("Asked to seek outside the file, valid offsets %r to %r" \
                                 % (0, length))
        #Find which block this is in...
        #TODO - Replace this simple list with a faster lookup structure
        for i, (comp_start, uncomp_start, unpadded_size) in enumerate(self._index):
            if offset < uncomp_start:
                #Overshot!
                i -= 1
                break
        print("Seeking to %i --> block %i, on disk from %i to %i, covering %i to %i decompressed." \
              % (offset, i, self._index[i][0], self._index[i+1][0], self._index[i][1], self._index[i+1][1]))
        self._load_block(i)
        self._within_block_offset = offset - self._index[i][1]
        return offset

    def _load_block(self, block_number=None):
        if block_number is None:
            block_number = self._block + 1
        print("Loading block %i" % block_number)
        if block_number+1 == len(self._index):
            #End of file!
            self._buffer = _empty_bytes_string
            self._block = block_number
            return

        #Must hit the disk... first check cache limits,
        while len(self._buffers) >= self.max_cache:
            #TODO - Implemente LRU cache removal?
            self._buffers.popitem()

        block_start = self._index[block_number][0]
        block_size = self._index[block_number+1][0] - block_start
        if block_size != self._index[block_number][2]:
            #print("Hmm. Block size %i, not %i" % (self._index[block_number][2], block_size))
            block_size = self._index[block_number][2]
            if block_size % 4 and block_size + 4 - (block_size % 4) != self._index[block_number+1][0] - block_start:
                print("Hmm. Block size %i (or %i with padding), not %i" \
                      % (block_size, block_size + 4 - (block_size % 4),
                         self._index[block_number+1][0] - block_start))
        uncomp_size = self._index[block_number+1][1] - self._index[block_number][1]
        self._handle.seek(block_start)
        block_header_len, filters = _load_stream_block_header(self._handle, block_size, uncomp_size)
        assert self._handle.tell() == block_start + block_header_len
        if block_size % 4:
            pad = 4 - (block_size % 4)
        else:
            pad = 0
        #Unpadded Size is the size of the Block Header, Compressed Data, and Check fields.
        #TODO - Set check size according to checksum being used, here 8 for CRC64
        data = self._handle.read(block_size - block_header_len - 8 + pad)
        print("Loading block %i, raw size on disk was %i (plus %i pad, less %i header)" % (block_number, block_size, pad, block_header_len))
        #print("Loading block %i, raw is %r" % (block_number, data))
        if pad:
            assert data[-pad:] == _null * pad, "Block ends %r but expected %i null padding" % (data[-pad:], pad)
        if _decompress:
            print("Decompressing block %i, using %i bytes, filters %r" % (block_number, len(data), filters))
            print("%r" % data)
            data = _decompress(data, format=FORMAT_RAW, filters=filters)
            #data = _decompress(self._magic + data + self._magic_foot, format=FORMAT_XY)
            #data = _decompress(self._magic + data, format=FORMAT_XY)
            #data = _decompress(data, format=FORMAT_RAW, filters=None)
            #data = _decompress_block(data, uncomp_size)
            print("Block starts: %r" % data[:100])
            assert len(data) == self._index[block_number+1][1] - self._index[block_number][1]
        else:
            print("Can't decompress with %r" % _decompress)
        self._block = block_number
        self._buffer = data
        self._buffers[block_number] = data

    def read(self, size=-1):
        if size < 0:
            raise NotImplementedError("Don't be greedy, that could be massive!")
        elif size == 0:
            if self._text:
                return ""
            else:
                return _empty_bytes_string
        elif self._within_block_offset + size <= len(self._buffer):
            #This may leave us right at the end of a block
            #(lazy loading, don't load the next block unless we have too)
            data = self._buffer[self._within_block_offset:self._within_block_offset + size]
            self._within_block_offset += size
            assert data #Must be at least 1 byte
            return data
        else:
            data = self._buffer[self._within_block_offset:]
            size -= len(data)
            self._load_block() #will reset offsets
            #TODO - Test with corner case of an empty block followed by
            #a non-empty block
            if not self._buffer:
                return data #EOF
            elif size:
                #TODO - Avoid recursion
                return data + self.read(size)
            else:
                #Only needed the end of the last block
                return data

    def close(self):
        self._handle.close()
        self._block_start_offset = None
        self._buffers = None
        self._index = None

    def seekable(self):
        return True

    def isatty(self):
        return False

    def fileno(self):
        return self._handle.fileno()


for f in ["../maf/chr19_gl000208_random.maf.xz",
          "../maf/chr19_gl000208_random.maf.b1k.xz",
          "../maf/chr19_gl000209_random.maf.xz",
          "../maf/chr19_gl000209_random.maf.b10k.xz",
          "../maf/chrY.maf.xz",
          "../maf/chrY.maf.b1M.xz",
          "thousand_blastx_nr.xml.xz",
          "thousand_blastx_nr.xml.s1M.xz",
          "thousand_blastx_nr.xml.b1M.xz"]:
    print("="*78)
    print(f)
    #h = open(f, "rb")
    #blocks = _load_index(h)
    try:
        h = XzReader(f, max_block_size=1048576)
    except ValueError as e:
        print(e)
        continue
    assert 2000 == h.seek(2000)
    if len(h._index) > 3:
        print(h._index[0])
        print(h._index[1])
        print("...")
        print(h._index[-1])
    print(h.read(100))
    print("Done")
    h.close()
    print("")
