# Copyright 2012-13 by Peter Cock.
# All rights reserved.

import os
import unittest

from bxz import XzReader, _load_index

class TestBlocked(unittest.TestCase):

    def check(self, filename, exp_streams, exp_blocks):
        if not os.path.isfile(filename):
            print("missing %s" % filename)
            return
        h = open(filename, "rb")
        blocks, stream_count, max_uncomp_block = _load_index(h)
        h.close()
        self.assertEqual(exp_streams, stream_count)
        self.assertEqual(exp_blocks, len(blocks) - 1)

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
        self.check(filename, 1, 1)

    def test_Lorem_Ipsum_6s_6b(self):
        filename = "Lorem_Ipsum.txt.s1k.xz"
        self.check(filename, 6, 6)

    def test_Lorem_Ipsum_1s_6b_sha256(self):
        filename = "Lorem_Ipsum.txt.b1k.sha256.xz"
        self.check(filename, 1, 6)

    def test_Lorem_Ipsum_1s_6b_crc32(self):
        filename = "Lorem_Ipsum.txt.b1k.crc32.xz"
        self.check(filename, 1, 6)

    def test_Lorem_Ipsum_1s_6b_check_none(self):
        filename = "Lorem_Ipsum.txt.b1k.check_none.xz"
        self.check(filename, 1, 6)

    def test_Lorem_Ipsum_mixed_checksums(self):
        filename = "Lorem_Ipsum.txt.mixed1k.xz"
        with open(filename, "rb") as h:
            self.assertRaises(ValueError, _load_index, h)
        self.assertRaises(ValueError, XzReader, filename)

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
