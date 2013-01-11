# Copyright 2012-13 by Peter Cock.
# All rights reserved.

import os

from bxz import XzReader

for f in [# Default behaviour, one stream and one block:
          "Lorem_Ipsum.txt.xz",
          # Six streams each with one block of 1000 bytes:
          "Lorem_Ipsum.txt.s1k.xz",
          # One stream with six blocks of 1000 bytes:
          "Lorem_Ipsum.txt.b1k.xz",
          "Lorem_Ipsum.txt.b1k.check_none.xz"
          "Lorem_Ipsum.txt.b1k.crc32.xz",
          "Lorem_Ipsum.txt.b1k.sha256.xz",
          "../maf/chr19_gl000208_random.maf.xz",
          "../maf/chr19_gl000208_random.maf.b1k.xz",
          "../maf/chr19_gl000209_random.maf.xz",
          "../maf/chr19_gl000209_random.maf.b10k.xz",
          "../maf/chrY.maf.xz",
          "../maf/chrY.maf.b1M.xz",
          "thousand_blastx_nr.xml.xz",
          "thousand_blastx_nr.xml.s1M.xz",
          "thousand_blastx_nr.xml.b1M.xz"]:
    if not os.path.isfile(f):
        continue
    print("="*78)
    print(f)
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
