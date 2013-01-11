# Copyright 2012-13 by Peter Cock.
# All rights reserved.

import os
import unittest

try:
    from backports.lzma import CHECK_NONE, CHECK_CRC32, CHECK_CRC64, CHECK_SHA256
except ImportError:
    from lzma import CHECK_NONE, CHECK_CRC32, CHECK_CRC64, CHECK_SHA256

from bxz import XzReader, _load_index

class TestBlocked(unittest.TestCase):

    def check(self, filename, exp_streams, exp_blocks, exp_checksum=CHECK_CRC64):
        if not os.path.isfile(filename):
            print("missing %s" % filename)
            return
        h = open(filename, "rb")
        blocks, stream_count, max_uncomp_block = _load_index(h)
        h.close()
        self.assertEqual(exp_streams, stream_count)
        self.assertEqual(exp_blocks, len(blocks) - 1)
        checks = [row[3] for row in blocks[:-1]]
        if isinstance(exp_checksum, list):
            for exp, checksum in zip(exp_checksum, checks):
                self.assertEqual(checksum, exp)
        else:
            for checksum in checks:
                self.assertEqual(checksum, exp_checksum)

        try:
            h = XzReader(filename, max_block_size=1048576)
        except ValueError, e:
            if "(over the limit specified of 1048576)" in str(e):
                return
            raise
        self.assertEqual(2000, h.seek(2000))
        if len(h._index) > 3:
            block = h._index[0]
            block = h._index[1]
            block = h._index[-1]
        data = h.read(100)
        h.close()
    
    def test_Lorem_Ipsum_1s_1b(self):
        filename = "Lorem_Ipsum.txt.xz"
        self.check(filename, 1, 1, CHECK_CRC64)

    def test_Lorem_Ipsum_6s_6b(self):
        filename = "Lorem_Ipsum.txt.s1k.xz"
        self.check(filename, 6, 6, CHECK_CRC64)

    def test_Lorem_Ipsum_1s_6b_sha256(self):
        filename = "Lorem_Ipsum.txt.b1k.sha256.xz"
        self.check(filename, 1, 6, CHECK_SHA256)

    def test_Lorem_Ipsum_1s_6b_crc32(self):
        filename = "Lorem_Ipsum.txt.b1k.crc32.xz"
        self.check(filename, 1, 6, CHECK_CRC32)

    def test_Lorem_Ipsum_1s_6b_check_none(self):
        filename = "Lorem_Ipsum.txt.b1k.check_none.xz"
        self.check(filename, 1, 6, CHECK_NONE)

    def test_Lorem_Ipsum_mixed_checksums(self):
        filename = "Lorem_Ipsum.txt.mixed1k.xz"
        self.check(filename, 6, 6, [CHECK_CRC64, CHECK_CRC32, CHECK_SHA256,
                                    CHECK_NONE, CHECK_CRC32, CHECK_CRC64])

    def test_maf_chr19(self):
        if not os.path.isdir("../maf"):
            print("missing MAF examples")
            return
        self.check("../maf/chr19_gl000208_random.maf.xz", 1, 1)
        self.check("../maf/chr19_gl000208_random.maf.b1k.xz", 1, 5)
        self.check("../maf/chr19_gl000209_random.maf.xz", 1, 1)
        self.check("../maf/chr19_gl000209_random.maf.b10k.xz", 1, 266)
        self.check("../maf/chrY.maf.xz", 1, 1)
        self.check("../maf/chrY.maf.b1M.xz", 1, 316)

    def test_thousand_blastx_nr_xml(self):
        self.check("thousand_blastx_nr.xml.xz", 1, 1)
        self.check("thousand_blastx_nr.xml.s1M.xz", 286, 286)
        self.check("thousand_blastx_nr.xml.b1M.xz", 1, 286)

if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity = 2)
    unittest.main(testRunner=runner)
