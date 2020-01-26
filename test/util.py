# -*- coding: utf-8 -*-
"""
(c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php

Test helpers.
"""

import sys
import time

# # ==============================================================================
# # write_test_file
# # ==============================================================================


# def write_test_file(name, size):
#     path = os.path.join(gettempdir(), name)
#     with open(path, "wb") as f:
#         f.write(compat.to_bytes("*") * size)
#     return path

# ========================================================================
# Timing
# ========================================================================


class Timing:
    """Print timing"""

    def __init__(self, name, count=None, fmt=None, count2=None, fmt2=None, stream=None):
        self.name = name
        self.count = count
        self.fmt = fmt
        self.count2 = count2
        self.fmt2 = fmt2
        self.stream = stream or sys.stdout

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        elap = time.time() - self.start
        msg = ["Timing {:<20} took {:>6.3f} sec".format(repr(self.name), elap)]
        if self.count:
            fmt = self.fmt or "{:0,.1f} bytes/sec"
            msg.append(fmt.format(float(self.count) / elap))
        if self.count2:
            fmt = self.fmt2 or "{:0,.1f} bytes/sec"
            msg.append(fmt.format(float(self.count2) / elap))
        print(", ".join(msg))
